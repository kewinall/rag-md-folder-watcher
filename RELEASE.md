# Release Guide

## 建立版本

1. 更新 `VERSION`、`pyproject.toml`、`app/version.py` 與 `CHANGELOG.md`。
2. 執行完整測試：

   ```bash
   python -m pytest -q
   ```

3. 建立 commit 與 tag：

   ```bash
   git add .
   git commit -m "release: v1.0.1"
   git tag -a v1.0.1 -m "Release v1.0.1"
   git push origin main
   git push origin v1.0.1
   ```

4. `.github/workflows/release.yml` 會：
   - 建置並推送 `ghcr.io/<owner>/<repository>`。
   - 建立 `1.0.1`、`1.0`、`1` 與 `latest` tags。
   - 建立 GitHub Release。
   - 附加 source ZIP 與 SHA-256 檔。

## 第一次使用 GHCR

Repository Actions 必須允許 `GITHUB_TOKEN` 寫入 Packages。Workflow 已宣告：

```yaml
permissions:
  contents: write
  packages: write
```

發布後可在 package 設定中調整 public/private visibility。
