# First Upload to GitHub

## 1. Create an empty repository

Recommended repository name:

```text
rag-md-folder-watcher
```

When creating it on GitHub, do not initialize README, `.gitignore` or License because they are already included.

## 2. Review before upload

```bash
git status
find . -maxdepth 3 -type f | sort
```

Confirm the repository does not contain `.env`, runtime `data/`, credentials, internal documents or customer files.

## 3. Initialize and push

```bash
git init
git branch -M main
git add .
git commit -m "feat: initial release v1.0.1"
git remote add origin https://github.com/<github-account>/rag-md-folder-watcher.git
git push -u origin main
```

## 4. Create the first release

```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

The release workflow will run tests, publish the GHCR image, create a GitHub Release and attach the ZIP/checksum files.

## 5. Recommended repository settings

- Start as **Private** until source ownership and test fixtures are reviewed.
- Enable **Private vulnerability reporting** under Security settings.
- Protect `main` and require the `CI / test` and `CI / container-build` checks before merge.
- Keep Actions workflow permissions restricted; the Release workflow explicitly requests package and release write access.
