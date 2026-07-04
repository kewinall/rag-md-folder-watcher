# Changelog

本專案依照 [Semantic Versioning](https://semver.org/) 管理版本。

## [1.0.1] - 2026-07-04

### Fixed

- 修正 Word 內嵌 EMF、WMF、WDP、SVG 或異常圖片造成的 `UnidentifiedImageError`。
- SVG 會先渲染成 PNG，再交由 OCR 處理。
- Linux/Pillow 無法可靠解碼的特殊圖片改為安全略過，不再使整份文件失敗。
- Word 與 PowerPoint 圖片使用 SHA-256 去重，避免重複 OCR。

### Changed

- 無 OCR 文字的圖片不再產生大量低價值 Markdown 段落。
- 圖片 OCR 結果改為摘要式警告，降低 metadata 與 token 用量。

## [1.0.0] - 2026-07-04

### Added

- 容器啟動後自動監控掛載資料夾。
- 自動辨識 Word、Excel、PowerPoint、PDF、HTML、文字、結構化資料及圖片。
- 圖片與掃描型 PDF OCR。
- 舊版 `.doc/.xls/.ppt` 經 LibreOffice headless 轉換。
- `input/processing/output/archive/failed/state/logs` 作業目錄。
- Markdown、metadata JSON 與 `.done` 完成標記。
- Windows 11、一般 Linux 與 Rocky Linux 9/SELinux 部署設定。
- 非 root、唯讀 root filesystem、capability drop 與資源限制。
