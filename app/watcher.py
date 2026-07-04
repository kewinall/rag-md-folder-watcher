from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import time
import traceback
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag_md_converter.pipeline import convert_one
from rag_md_converter.utils import sha256_file

from .detector import Detection, validate_detected_format
from .logging_config import configure_logging
from .settings import Settings
from .state import ProcessedIndex

LOGGER = logging.getLogger("rag_md_watcher")
TEMP_SUFFIXES = {
    ".tmp", ".part", ".partial", ".crdownload", ".uploading", ".download"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def unique_target(path: Path) -> Path:
    if not path.exists():
        return path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return path.with_name(f"{path.stem}__{timestamp}{path.suffix}")


class FolderWatcher:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.running = True
        self.observations: dict[Path, tuple[int, int, int]] = {}
        self.ignored_at_start: dict[Path, tuple[int, int]] = {}
        self.index = ProcessedIndex(settings.state_dir / "processed.jsonl")
        self._ensure_directories()

        if not settings.process_existing_on_start:
            for existing in self._iter_input_files():
                try:
                    stat = existing.stat()
                except OSError:
                    continue
                self.ignored_at_start[existing] = (stat.st_size, stat.st_mtime_ns)

    def _ensure_directories(self) -> None:
        for directory in (
            self.settings.input_dir,
            self.settings.processing_dir,
            self.settings.output_dir,
            self.settings.archive_dir,
            self.settings.failed_dir,
            self.settings.state_dir,
            self.settings.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def stop(self, *_: object) -> None:
        LOGGER.info("收到停止訊號")
        self.running = False

    def _iter_files(self, root: Path) -> list[Path]:
        iterator = root.rglob("*") if self.settings.recursive else root.glob("*")
        return sorted(
            path for path in iterator
            if path.is_file() and not path.is_symlink()
        )

    def _iter_input_files(self) -> list[Path]:
        files = []
        for path in self._iter_files(self.settings.input_dir):
            if path.name.startswith(".") or path.name.startswith("~$"):
                continue
            if path.suffix.lower() in TEMP_SUFFIXES:
                continue
            files.append(path)
        return files

    def _relative_path(self, path: Path, root: Path) -> Path:
        try:
            return path.relative_to(root)
        except ValueError:
            return Path(path.name)

    def _is_stable(self, path: Path) -> bool:
        try:
            stat = path.stat()
        except OSError:
            self.observations.pop(path, None)
            return False

        previous = self.observations.get(path)
        if previous and previous[0] == stat.st_size and previous[1] == stat.st_mtime_ns:
            unchanged = previous[2] + 1
        else:
            unchanged = 0

        self.observations[path] = (stat.st_size, stat.st_mtime_ns, unchanged)
        return unchanged >= self.settings.stable_checks

    def _move(self, source: Path, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        final_target = unique_target(target)
        shutil.move(str(source), str(final_target))
        return final_target

    def _write_failure(
        self,
        source: Path,
        relative_path: Path,
        error: str,
        details: str | None = None,
    ) -> None:
        failed_target = self._move(
            source,
            self.settings.failed_dir / relative_path,
        )
        payload = {
            "status": "failed",
            "source_file": relative_path.as_posix(),
            "failed_file": str(failed_target.relative_to(self.settings.data_root)),
            "error": error,
            "details": details,
            "failed_at": utc_now(),
        }
        atomic_json_write(
            failed_target.with_name(f"{failed_target.name}.error.json"),
            payload,
        )
        LOGGER.error("轉換失敗：%s：%s", relative_path, error)

    def _archive(self, source: Path, relative_path: Path) -> Path | None:
        if not self.settings.archive_source:
            source.unlink(missing_ok=True)
            return None
        return self._move(source, self.settings.archive_dir / relative_path)

    def _write_success_artifacts(
        self,
        output_path: Path,
        metadata: dict[str, Any],
    ) -> None:
        if self.settings.write_metadata:
            atomic_json_write(
                output_path.with_name(f"{output_path.name}.metadata.json"),
                metadata,
            )
        if self.settings.write_done_marker:
            atomic_json_write(
                output_path.with_name(f"{output_path.name}.done"),
                {
                    "status": "done",
                    "output_file": str(output_path.relative_to(self.settings.data_root)),
                    "source_sha256": metadata["source_sha256"],
                    "completed_at": metadata["completed_at"],
                },
            )

    def _process_claimed(self, source: Path, relative_path: Path) -> None:
        started_time = time.monotonic()
        started_at = utc_now()

        try:
            detection: Detection = validate_detected_format(source)
            source_hash = sha256_file(source)
            source_size = source.stat().st_size

            if self.settings.deduplicate:
                prior = self.index.get(source_hash)
                if prior:
                    archived_path = self._archive(source, relative_path)
                    duplicate_payload = {
                        "status": "duplicate",
                        "source_file": relative_path.as_posix(),
                        "source_sha256": source_hash,
                        "previous_output": prior.get("output_file"),
                        "archive_file": (
                            str(archived_path.relative_to(self.settings.data_root))
                            if archived_path else None
                        ),
                        "completed_at": utc_now(),
                    }
                    duplicate_target = (
                        self.settings.output_dir / relative_path.parent /
                        f"{relative_path.name}.duplicate.json"
                    )
                    atomic_json_write(unique_target(duplicate_target), duplicate_payload)
                    LOGGER.info("略過重複內容：%s", relative_path)
                    return

            output_directory = self.settings.output_dir / relative_path.parent
            converter_config = replace(
                self.settings.converter,
                output_dir=output_directory,
            )
            result = convert_one(source, converter_config)

            if not result.success or result.output_path is None:
                self._write_failure(
                    source,
                    relative_path,
                    result.error or "未知轉換錯誤",
                    "\n".join(result.warnings),
                )
                return

            archived_path = self._archive(source, relative_path)
            completed_at = utc_now()
            metadata = {
                "status": "done",
                "source_file": relative_path.as_posix(),
                "source_sha256": source_hash,
                "source_size_bytes": source_size,
                "detected_kind": detection.kind,
                "detection_confidence": detection.confidence,
                "converter": result.converter,
                "output_file": str(result.output_path.relative_to(self.settings.data_root)),
                "archive_file": (
                    str(archived_path.relative_to(self.settings.data_root))
                    if archived_path else None
                ),
                "chars_written": result.chars_written,
                "warnings": result.warnings,
                "started_at": started_at,
                "completed_at": completed_at,
                "elapsed_seconds": round(time.monotonic() - started_time, 3),
            }
            self._write_success_artifacts(result.output_path, metadata)
            self.index.append(metadata)
            LOGGER.info(
                "轉換完成：%s -> %s（%.3f 秒）",
                relative_path,
                result.output_path.relative_to(self.settings.output_dir),
                metadata["elapsed_seconds"],
            )
        except Exception as exc:
            self._write_failure(
                source,
                relative_path,
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )

    def process_input_file(self, input_path: Path) -> None:
        relative_path = self._relative_path(input_path, self.settings.input_dir)
        claimed_target = self.settings.processing_dir / relative_path
        try:
            claimed = self._move(input_path, claimed_target)
        except FileNotFoundError:
            return
        except OSError as exc:
            LOGGER.warning("無法取得檔案處理權：%s：%s", input_path, exc)
            return

        self.observations.pop(input_path, None)
        self._process_claimed(claimed, relative_path)

    def recover_processing_files(self) -> None:
        for source in self._iter_files(self.settings.processing_dir):
            relative_path = self._relative_path(source, self.settings.processing_dir)
            LOGGER.warning("接續處理上次未完成檔案：%s", relative_path)
            self._process_claimed(source, relative_path)

    def write_heartbeat(self, status: str = "running") -> None:
        atomic_json_write(
            self.settings.state_dir / "heartbeat.json",
            {
                "status": status,
                "pid": os.getpid(),
                "updated_at": utc_now(),
                "input_dir": str(self.settings.input_dir),
            },
        )

    def run_once(self) -> None:
        candidates = self._iter_input_files()
        current = set(candidates)
        for observed in list(self.observations):
            if observed not in current:
                self.observations.pop(observed, None)

        for input_path in candidates:
            initial_state = self.ignored_at_start.get(input_path)
            if initial_state is not None:
                try:
                    stat = input_path.stat()
                    current_state = (stat.st_size, stat.st_mtime_ns)
                except OSError:
                    self.ignored_at_start.pop(input_path, None)
                    continue
                if current_state == initial_state:
                    continue
                self.ignored_at_start.pop(input_path, None)
            if not self.running:
                break
            if self._is_stable(input_path):
                self.process_input_file(input_path)

        self.write_heartbeat()

    def run_forever(self) -> None:
        self.recover_processing_files()
        LOGGER.info(
            "開始監控 %s；遞迴=%s；間隔=%.1f 秒；OCR=%s；LibreOffice=%s",
            self.settings.input_dir,
            self.settings.recursive,
            self.settings.poll_interval_seconds,
            self.settings.converter.ocr,
            self.settings.converter.enable_libreoffice,
        )

        while self.running:
            cycle_started = time.monotonic()
            try:
                self.run_once()
            except Exception:
                LOGGER.exception("監控週期發生未預期錯誤")

            elapsed = time.monotonic() - cycle_started
            remaining = max(0.1, self.settings.poll_interval_seconds - elapsed)
            time.sleep(remaining)

        self.write_heartbeat(status="stopped")
        LOGGER.info("資料夾監控已停止")


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.logs_dir, settings.log_level)
    watcher = FolderWatcher(settings)
    signal.signal(signal.SIGTERM, watcher.stop)
    signal.signal(signal.SIGINT, watcher.stop)
    watcher.run_forever()


if __name__ == "__main__":
    main()
