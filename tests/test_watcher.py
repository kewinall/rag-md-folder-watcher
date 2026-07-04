from __future__ import annotations

import shutil
from pathlib import Path

from app.settings import Settings
from app.watcher import FolderWatcher


SUPPORTED = {
    ".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt",
    ".pdf", ".html", ".txt", ".csv", ".json", ".xml",
    ".md", ".png", ".jpg",
}


def configure(monkeypatch, root: Path) -> Settings:
    monkeypatch.setenv("DATA_ROOT", str(root))
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "0.01")
    monkeypatch.setenv("STABLE_CHECKS", "0")
    monkeypatch.setenv("WATCH_RECURSIVE", "true")
    monkeypatch.setenv("OCR_ENABLED", "true")
    monkeypatch.setenv("OCR_LANG", "eng")
    monkeypatch.setenv("ENABLE_LIBREOFFICE", "true")
    monkeypatch.setenv("ARCHIVE_SOURCE", "true")
    monkeypatch.setenv("WRITE_METADATA", "true")
    monkeypatch.setenv("WRITE_DONE_MARKER", "true")
    monkeypatch.setenv("DEDUPLICATE", "false")
    return Settings.from_env()


def test_all_supported_formats_are_converted(monkeypatch, tmp_path: Path) -> None:
    settings = configure(monkeypatch, tmp_path / "data")
    fixtures = Path(__file__).parent / "fixtures"
    nested_input = settings.input_dir / "department-a"
    nested_input.mkdir(parents=True)

    source_files = [path for path in fixtures.iterdir() if path.suffix.lower() in SUPPORTED]
    assert len(source_files) == 15
    for source in source_files:
        shutil.copy2(source, nested_input / source.name)

    watcher = FolderWatcher(settings)
    watcher.run_once()

    markdown_files = list(settings.output_dir.rglob("*.md"))
    metadata_files = list(settings.output_dir.rglob("*.metadata.json"))
    done_files = list(settings.output_dir.rglob("*.done"))
    archived_files = [
        path for path in settings.archive_dir.rglob("*")
        if path.is_file()
    ]
    failed_source_files = [
        path for path in settings.failed_dir.rglob("*")
        if path.is_file() and not path.name.endswith(".error.json")
    ]

    assert len(markdown_files) == 15
    assert len(metadata_files) == 15
    assert len(done_files) == 15
    assert len(archived_files) == 15
    assert not failed_source_files

    success_rate = len(markdown_files) / len(source_files)
    assert success_rate >= 0.90


def test_wrong_extension_is_rejected(monkeypatch, tmp_path: Path) -> None:
    settings = configure(monkeypatch, tmp_path / "data")
    settings.input_dir.mkdir(parents=True)
    fixture = Path(__file__).parent / "fixtures" / "sample.pdf"
    shutil.copy2(fixture, settings.input_dir / "renamed.txt")

    watcher = FolderWatcher(settings)
    watcher.run_once()

    assert not list(settings.output_dir.rglob("*.md"))
    assert list(settings.failed_dir.rglob("renamed.txt"))
    assert list(settings.failed_dir.rglob("*.error.json"))


def test_temporary_upload_file_is_ignored(monkeypatch, tmp_path: Path) -> None:
    settings = configure(monkeypatch, tmp_path / "data")
    settings.input_dir.mkdir(parents=True)
    pending = settings.input_dir / "sample.pdf.uploading"
    pending.write_bytes(b"partial")

    watcher = FolderWatcher(settings)
    watcher.run_once()

    assert pending.exists()
    assert not list(settings.output_dir.rglob("*.md"))


def test_processing_recovery(monkeypatch, tmp_path: Path) -> None:
    settings = configure(monkeypatch, tmp_path / "data")
    settings.processing_dir.mkdir(parents=True)
    fixture = Path(__file__).parent / "fixtures" / "sample.txt"
    shutil.copy2(fixture, settings.processing_dir / "sample.txt")

    watcher = FolderWatcher(settings)
    watcher.recover_processing_files()

    assert list(settings.output_dir.rglob("*.md"))
    assert list(settings.archive_dir.rglob("sample.txt"))


def test_background_process_detects_new_file(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys
    import time

    root = tmp_path / "background-data"
    environment = os.environ.copy()
    environment.update(
        {
            "DATA_ROOT": str(root),
            "POLL_INTERVAL_SECONDS": "0.1",
            "STABLE_CHECKS": "0",
            "OCR_ENABLED": "true",
            "OCR_LANG": "eng",
            "ENABLE_LIBREOFFICE": "true",
            "LOG_LEVEL": "INFO",
        }
    )

    process = subprocess.Popen(
        [sys.executable, "-m", "app.watcher"],
        cwd=Path(__file__).parents[1],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.time() + 15
        heartbeat = root / "state" / "heartbeat.json"
        while time.time() < deadline and not heartbeat.exists():
            time.sleep(0.1)
        assert heartbeat.exists()

        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__).parent / "fixtures" / "sample.txt", input_dir)

        outputs = []
        while time.time() < deadline:
            outputs = list((root / "output").rglob("*.md"))
            if outputs:
                break
            time.sleep(0.1)

        assert outputs
        assert list((root / "archive").rglob("sample.txt"))
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_scanned_pdf_uses_ocr(monkeypatch, tmp_path: Path) -> None:
    from PIL import Image

    settings = configure(monkeypatch, tmp_path / "data")
    settings.input_dir.mkdir(parents=True)
    source_image = Image.open(Path(__file__).parent / "fixtures" / "sample.png").convert("RGB")
    scanned_pdf = settings.input_dir / "scanned.pdf"
    source_image.save(scanned_pdf, "PDF", resolution=150.0)
    source_image.close()

    watcher = FolderWatcher(settings)
    watcher.run_once()

    outputs = list(settings.output_dir.rglob("scanned.pdf.md"))
    assert outputs
    content = outputs[0].read_text(encoding="utf-8")
    assert "IMAGE RAG TEXT" in content


def test_docx_vector_image_does_not_raise_unidentified_image(monkeypatch, tmp_path: Path) -> None:
    import zipfile
    import xml.etree.ElementTree as ET

    settings = configure(monkeypatch, tmp_path / "data")
    settings.input_dir.mkdir(parents=True)
    source_docx = Path(__file__).parent / "fixtures" / "sample.docx"
    modified_docx = settings.input_dir / "vector-image.docx"
    unpacked = tmp_path / "docx-unpacked"

    with zipfile.ZipFile(source_docx) as archive:
        archive.extractall(unpacked)

    media_dir = unpacked / "word" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    (media_dir / "unsupported.emf").write_bytes(b"not-a-real-emf")

    content_types_path = unpacked / "[Content_Types].xml"
    content_types_tree = ET.parse(content_types_path)
    content_types_root = content_types_tree.getroot()
    content_types_ns = content_types_root.tag.split("}")[0].strip("{")
    ET.SubElement(
        content_types_root,
        f"{{{content_types_ns}}}Default",
        Extension="emf",
        ContentType="image/x-emf",
    )
    content_types_tree.write(content_types_path, encoding="utf-8", xml_declaration=True)

    rels_path = unpacked / "word" / "_rels" / "document.xml.rels"
    rels_tree = ET.parse(rels_path)
    rels_root = rels_tree.getroot()
    rels_ns = rels_root.tag.split("}")[0].strip("{")
    ET.SubElement(
        rels_root,
        f"{{{rels_ns}}}Relationship",
        Id="rIdUnsupportedEmf",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
        Target="media/unsupported.emf",
    )
    rels_tree.write(rels_path, encoding="utf-8", xml_declaration=True)

    with zipfile.ZipFile(modified_docx, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in unpacked.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(unpacked))

    watcher = FolderWatcher(settings)
    watcher.run_once()

    outputs = list(settings.output_dir.rglob("vector-image.docx.md"))
    assert outputs
    content = outputs[0].read_text(encoding="utf-8")
    assert "UnidentifiedImageError" not in content
    assert "略過不支援 1 張" in content
    assert not list(settings.failed_dir.rglob("vector-image.docx"))
