# Security Design

## Existing controls

- Allowlisted extensions and signature/OOXML validation.
- Symbolic links are not followed.
- OOXML member count, expanded size and traversal checks.
- `defusedxml` for XML parsing.
- HTML scripts, styles and iframes are removed; remote resources are not fetched.
- File size, PDF page, OCR page, image pixel, table row/column and output character limits.
- LibreOffice runs headless with an isolated temporary profile and timeout.
- OCR and LibreOffice failures are isolated to the source file or embedded object.
- Container runs without root, has a read-only root filesystem, drops all capabilities and enables `no-new-privileges`.
- CPU, memory and PID limits are defined in Compose.
- No API and no exposed port.

## Deployment requirements

- Mount only the dedicated data directory at `/data`.
- Never mount `/`, `/etc`, home directories, Docker socket or credential directories.
- Keep SELinux enforcing on Rocky Linux and use `compose.rocky.yaml`.
- Place antivirus or content-disarm controls before `input` when processing untrusted public uploads.
- Restrict host filesystem permissions for `input`, `output`, `archive` and `failed`.
- Back up only data that must be retained; define retention for source and failed files.
- Rebuild regularly to receive base image and OS package updates.

## Residual risks

Document parsing libraries and LibreOffice may contain undiscovered vulnerabilities. Containers reduce but do not eliminate host risk. Highly hostile documents should be processed on a dedicated VM or sandbox with no outbound network and disposable storage.
