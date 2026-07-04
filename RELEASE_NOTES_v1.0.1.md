# v1.0.1 — Embedded image OCR compatibility

## Fixed

- Prevents Word documents containing unsupported EMF, WMF, WDP, OLE preview or malformed image objects from failing with `UnidentifiedImageError`.
- Renders SVG content to PNG before OCR.
- Safely skips image types that Pillow cannot decode reliably on Linux.
- Applies the same embedded-image handling to PowerPoint.

## Improved

- Deduplicates embedded images by SHA-256 before OCR.
- Omits empty OCR sections from Markdown to reduce low-value tokens.
- Records compact OCR summaries and warnings in metadata.

## Validation

- Fifteen source formats passed: DOCX, XLSX, PPTX, DOC, XLS, PPT, PDF, HTML, TXT, CSV, JSON, XML, MD, PNG and JPG.
- Pytest result: `7 passed`.
