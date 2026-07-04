# Troubleshooting

## Container is unhealthy

```bash
docker compose ps
docker compose logs --tail=200 rag-md-watcher
cat <data-dir>/state/heartbeat.json
```

Check that the mounted directory is writable by `CONTAINER_UID:CONTAINER_GID`.

## Permission denied on Rocky Linux

Use the SELinux override:

```bash
docker compose -f compose.yaml -f compose.rocky.yaml up -d --build
```

Also confirm host ownership:

```bash
id -u
id -g
sudo chown -R <uid>:<gid> /opt/rag-md-data
```

## File remains in input

- Confirm it does not end in `.tmp`, `.part`, `.partial`, `.crdownload`, `.uploading` or `.download`.
- Wait for `STABLE_CHECKS` polling cycles.
- Confirm it is not a symbolic link.
- Inspect logs for permission errors.

## File moved to failed

Open the matching `*.error.json` under `failed`. Typical causes are unsupported extension, extension/signature mismatch, size limits, malformed OOXML, parser timeout or password-protected content.

## Word embedded image warning

EMF, WMF, WDP and some OLE previews are not reliably decodable by Pillow on Linux. Version 1.0.1 skips them and records a summary. This does not fail the whole document.

## Reprocess a file

With `DEDUPLICATE=false`, place the archived source back into `input`. If output already exists and `OVERWRITE_OUTPUT=false`, a short SHA-256 suffix is added.
