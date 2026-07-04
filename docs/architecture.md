# Architecture

```text
Host mounted directory
├── input         user drop zone
├── processing    claimed files
├── output        Markdown, metadata, done marker
├── archive       successfully processed sources
├── failed        rejected/failed sources and error JSON
├── state         heartbeat and processed index
└── logs          rotating watcher log
```

## Processing sequence

1. Poll `input`, recursively by default.
2. Ignore temporary suffixes and symbolic links.
3. Wait until size and modification time remain stable.
4. Move the file to `processing` to claim it.
5. Validate extension against file signatures/OOXML structure.
6. Select a format-specific converter.
7. Write Markdown atomically, then metadata and `.done` marker.
8. Move the source to `archive`; failures go to `failed`.
9. On restart, recover files left in `processing`.

## Module boundaries

- `app/`: directory monitoring, state, logging and lifecycle.
- `rag_md_converter/`: file validation and format-specific conversion.
- `tests/`: end-to-end watcher and parser regression tests.

There is no API, message broker, database or listening network port.
