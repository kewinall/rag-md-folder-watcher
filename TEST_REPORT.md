# Test Report

## Date

2026-07-04

## Scope

1. Folder watcher background monitoring and automatic processing.
2. Recursive subdirectories and relative path preservation.
3. Format selection and file signature/structure validation.
4. Markdown, metadata and done-marker output.
5. Successful source archiving.
6. Wrong-extension rejection and failed-file isolation.
7. Temporary `.uploading` file exclusion.
8. Recovery of files left under `processing`.
9. Image and scanned-PDF OCR.
10. LibreOffice conversion for `.doc/.xls/.ppt`.
11. Word unsupported vector-image regression handling.

## Format matrix

| Format | Result |
|---|---:|
| DOCX | Passed |
| XLSX | Passed |
| PPTX | Passed |
| DOC | Passed |
| XLS | Passed |
| PPT | Passed |
| PDF | Passed |
| HTML | Passed |
| TXT | Passed |
| CSV | Passed |
| JSON | Passed |
| XML | Passed |
| MD | Passed |
| PNG | Passed |
| JPG | Passed |

**Format pass rate: 15/15, 100%.**

## Pytest

```text
7 passed in 24.84s
```

## Validation boundary

The build environment used for this package does not expose a Docker or Podman daemon. The following checks were completed:

- Python integration and background-process tests
- Fifteen real sample-format conversions
- Scanned PDF OCR regression test
- Unsupported Word embedded-image regression test
- Dockerfile dependency-name review
- Compose and GitHub Actions YAML parsing

Run the included CI workflow or `docker compose build` on the target Windows 11 Docker Desktop or Rocky Linux 9 Docker host to validate the final container image in that environment.
