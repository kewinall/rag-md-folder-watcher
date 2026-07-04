# RAG Markdown Folder Watcher

容器化的文件前處理工具。容器啟動後會持續監控掛載目錄中的 `input`，自動辨識新檔案格式，並將內容轉成適合 RAG ingestion 的 Markdown。

- 不包含 API、資料庫或 message broker
- 不開放任何網路 port
- Windows 11 Docker Desktop、Rocky Linux 9 與一般 Linux 可使用
- OCR、掃描型 PDF 與舊版 Office 轉換預設開啟
- 每種格式由獨立 converter 處理，未使用 MarkItDown

目前版本：**1.0.1**

## Processing flow

```text
mounted-directory/input
          │
          ├─ wait until file copy is complete
          ├─ validate extension and actual file structure
          ▼
mounted-directory/processing
          │
          ├─ select format-specific converter
          ├─ OCR / LibreOffice / content cleanup
          ▼
mounted-directory/output
          ├─ filename.ext.md
          ├─ filename.ext.md.metadata.json
          └─ filename.ext.md.done

successful source → archive
failed source     → failed + error.json
```

## Supported formats

| Type | Extensions | Default behavior |
|---|---|---|
| Word | `.docx` | Paragraphs, headings, tables and embedded-image OCR |
| Legacy Word | `.doc` | Convert to `.docx` with LibreOffice, then parse |
| Excel | `.xlsx` | Convert worksheets to Markdown tables |
| Legacy Excel | `.xls` | Convert to `.xlsx` with LibreOffice, then parse |
| PowerPoint | `.pptx` | Slide text, tables and image OCR |
| Legacy PowerPoint | `.ppt` | Convert to `.pptx` with LibreOffice, then parse |
| PDF | `.pdf` | Extract text; OCR pages without usable text |
| HTML | `.html/.htm` | Remove script/style/iframe and convert to Markdown |
| Text | `.txt` | Encoding-tolerant text extraction |
| CSV | `.csv` | Detect delimiter and convert to Markdown table |
| JSON | `.json` | Pretty-print as structured Markdown content |
| XML | `.xml` | Parse with `defusedxml` and render a hierarchy |
| Markdown | `.md/.markdown` | Normalize Markdown |
| Images | `.png/.jpg/.jpeg` | Tesseract OCR with English and Traditional Chinese |

## Directory layout

Only one host directory is mounted. The container creates these subdirectories automatically:

```text
data/
├── input/       # users place files here
├── processing/  # files currently being processed
├── output/      # Markdown, metadata and done marker
├── archive/     # successfully processed source files
├── failed/      # failed/rejected files and error JSON
├── state/       # heartbeat and processed index
└── logs/        # watcher.log and rotated logs
```

Subdirectories under `input` are preserved in `output` and `archive`.

---

## Quick start: Windows 11

### Requirements

- Docker Desktop
- Linux containers
- WSL 2 backend recommended

### 1. Clone or download

```powershell
git clone https://github.com/<github-account>/rag-md-folder-watcher.git
Set-Location .\rag-md-folder-watcher
```

Or download a Release ZIP and extract it.

### 2. Create the mounted directory

```powershell
New-Item -ItemType Directory -Force C:\rag-md-data | Out-Null
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
HOST_DATA_DIR=C:/rag-md-data
CONTAINER_UID=1000
CONTAINER_GID=1000
```

Use `/` in the Windows path.

### 3. Start the container

```powershell
docker compose up -d --build
```

Or:

```powershell
.\scripts\start-windows.ps1
```

### 4. Drop a file into input

```powershell
Copy-Item C:\source\sample.pdf C:\rag-md-data\input\
```

Results:

```text
C:\rag-md-data\output\sample.pdf.md
C:\rag-md-data\output\sample.pdf.md.metadata.json
C:\rag-md-data\output\sample.pdf.md.done
C:\rag-md-data\archive\sample.pdf
```

### 5. Check status

```powershell
docker compose ps
docker compose logs -f rag-md-watcher
```

---

## Quick start: Rocky Linux 9

### 1. Clone repository

```bash
git clone https://github.com/<github-account>/rag-md-folder-watcher.git
cd rag-md-folder-watcher
```

### 2. Create data directory

```bash
sudo mkdir -p /opt/rag-md-data
sudo chown -R "$(id -u):$(id -g)" /opt/rag-md-data
cp .env.example .env
```

Check the current UID/GID:

```bash
id -u
id -g
```

Edit `.env`, for example:

```dotenv
HOST_DATA_DIR=/opt/rag-md-data
CONTAINER_UID=1000
CONTAINER_GID=1000
```

### 3. Start with SELinux volume labeling

```bash
docker compose \
  -f compose.yaml \
  -f compose.rocky.yaml \
  up -d --build
```

Or use the helper script, which detects SELinux:

```bash
./scripts/start-linux.sh
```

### 4. Drop a file into input

```bash
cp /path/to/sample.pdf /opt/rag-md-data/input/
```

### 5. Check status

```bash
docker compose ps
docker compose logs -f rag-md-watcher
find /opt/rag-md-data/output -type f
```

For Linux without SELinux:

```bash
docker compose up -d --build
```

---

## Use a prebuilt GHCR image

After publishing a Git tag, the included Release workflow builds an image such as:

```text
ghcr.io/<github-account>/rag-md-folder-watcher:1.0.1
```

Set `.env`:

```dotenv
IMAGE_NAME=ghcr.io/<github-account>/rag-md-folder-watcher
IMAGE_TAG=1.0.1
```

Then run without rebuilding by changing the service to use the image already defined by Compose:

```bash
docker compose pull
docker compose up -d --no-build
```

For a private package, authenticate first:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-account> --password-stdin
```

---

## Default enabled features

- Recursive monitoring of `input`
- Process files already present when the container starts
- PNG/JPG OCR
- Scanned PDF OCR
- Word and PowerPoint embedded-image OCR
- English and Traditional Chinese Tesseract languages
- `.doc/.xls/.ppt` conversion through LibreOffice
- HTML cleanup
- Excel and CSV Markdown tables
- Safe XML parsing
- Repeated short-line cleanup
- Metadata JSON
- `.done` completion marker
- Successful source archiving
- Failed-file isolation
- Recovery of files left in `processing` after restart
- Heartbeat and Docker healthcheck
- Rotating file logs and stdout logs

## Default guardrails

All features being enabled does not mean unlimited parsing. Defaults include:

| Limit | Default |
|---|---:|
| Source file | 100 MB |
| OOXML expanded size | 500 MB |
| OOXML members | 5,000 |
| Image pixels | 40 million |
| PDF pages | 500 |
| PDF OCR pages | 100 |
| Excel rows per worksheet | 5,000 |
| CSV rows | 10,000 |
| Markdown characters | 2,000,000 |
| OCR timeout | 120 seconds |
| LibreOffice timeout | 180 seconds |

These settings can be changed through `.env`.

## Common configuration

```dotenv
POLL_INTERVAL_SECONDS=3
STABLE_CHECKS=3
WATCH_RECURSIVE=true
PROCESS_EXISTING_ON_START=true

OCR_ENABLED=true
OCR_LANG=eng+chi_tra
OCR_TIMEOUT_SEC=120
PDF_OCR_DPI=200
PDF_OCR_MAX_PAGES=100

ENABLE_LIBREOFFICE=true
LIBREOFFICE_TIMEOUT_SEC=180

ARCHIVE_SOURCE=true
WRITE_METADATA=true
WRITE_DONE_MARKER=true
DEDUPLICATE=false
OVERWRITE_OUTPUT=false

MAX_FILE_MB=100
MAX_OUTPUT_CHARS=2000000
EXCEL_MAX_ROWS_PER_SHEET=5000
CSV_MAX_ROWS=10000
```

Recreate the container after changing `.env`:

```bash
docker compose up -d --force-recreate
```

## Safe file-copy behavior

The watcher waits until file size and modification time remain unchanged for multiple polling cycles. Temporary suffixes are ignored:

```text
.tmp .part .partial .crdownload .uploading .download
```

For large files or network shares, copy with a temporary suffix and rename only after the transfer completes.

Windows:

```powershell
Copy-Item .\large.pdf C:\rag-md-data\input\large.pdf.uploading
Rename-Item C:\rag-md-data\input\large.pdf.uploading large.pdf
```

Linux:

```bash
cp large.pdf /opt/rag-md-data/input/large.pdf.uploading
mv /opt/rag-md-data/input/large.pdf.uploading \
   /opt/rag-md-data/input/large.pdf
```

## Output naming

Input:

```text
input/department-a/annual-report.pdf
```

Output:

```text
output/department-a/annual-report.pdf.md
output/department-a/annual-report.pdf.md.metadata.json
output/department-a/annual-report.pdf.md.done
archive/department-a/annual-report.pdf
```

When output already exists and overwrite is disabled, the source SHA-256 prefix is added to avoid replacing an earlier version.

## Word embedded images

Word documents may contain EMF, WMF, SVG, WDP or OLE preview objects in addition to normal PNG/JPEG images.

Version 1.0.1 behavior:

- PNG, JPEG, TIFF, BMP, GIF and WebP are processed with Pillow/Tesseract.
- SVG is rendered to PNG before OCR.
- EMF, WMF, WDP and unsupported objects are safely skipped and summarized.
- Unsupported embedded images do not fail the whole Word document.
- Images with no recognized text do not produce low-value Markdown paragraphs.
- Duplicate embedded images are identified by SHA-256 and OCR runs only once.

## Development and tests

Python 3.12 is recommended.

Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

The integration matrix contains 15 formats:

```text
docx xlsx pptx doc xls ppt pdf html txt csv json xml md png jpg
```

Current result:

```text
7 passed
15/15 formats converted
```

## GitHub automation

The repository includes:

- `.github/workflows/ci.yml`
  - Runs the complete Python test suite
  - Builds the Docker image without pushing
- `.github/workflows/release.yml`
  - Triggered by a tag such as `v1.0.1`
  - Pushes semantic-version tags to GitHub Container Registry
  - Creates a GitHub Release
  - Attaches a source ZIP and SHA-256 checksum
- Dependabot for Python, Docker and GitHub Actions
- Bug and feature issue templates
- Pull request checklist

See [`RELEASE.md`](RELEASE.md) for release steps.

## Security

Key controls include:

- Extension allowlist and actual file-structure validation
- No symbolic-link following
- OOXML zip-bomb and path-traversal controls
- `defusedxml` for XML
- No remote HTML resource downloads
- Non-root container
- Read-only root filesystem
- All Linux capabilities dropped
- `no-new-privileges`
- CPU, memory and PID limits
- No API and no exposed port

No document parser can be guaranteed vulnerability-free. For untrusted public uploads, use an antivirus/content-disarm stage and a dedicated isolated host or VM.

See [`SECURITY.md`](SECURITY.md) and [`docs/security.md`](docs/security.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Security design](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Contributing](CONTRIBUTING.md)
- [Release guide](RELEASE.md)
- [Changelog](CHANGELOG.md)
- [Test report](TEST_REPORT.md)

## License

Apache License 2.0. Confirm that you have the right to publish the source code and test fixtures before changing a company-internal repository to public visibility.
