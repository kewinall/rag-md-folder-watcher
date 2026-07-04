# Contributing

## 開發環境

建議使用 Python 3.12。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

Windows PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

完整測試需要系統已安裝 LibreOffice、Tesseract 英文語言包與繁體中文語言包。

## 修改原則

- 每種來源格式維持獨立 converter。
- 不在 parser 中下載外部資源。
- 新增格式時同步更新 allowlist、格式驗證、README 與測試 fixture。
- 不將真實客戶、公司或個人文件提交至 repository。
- 錯誤應隔離單一檔案，不應使 watcher 主程序停止。
- 會增加 Markdown 大小的功能，需考慮 token 與重複內容控制。

## Commit message

建議採用 Conventional Commits：

```text
feat: add odt conversion
fix: skip unsupported embedded image
security: tighten OOXML limits
docs: update Rocky Linux deployment
```

## Pull request

PR 需至少包含：

- 問題與修改說明
- 測試結果
- 是否影響既有輸出格式
- 是否新增環境變數
- 是否涉及安全邊界
