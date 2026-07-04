# Security Policy

## Supported versions

| Version | Security updates |
|---|---|
| 1.0.x | Supported |
| < 1.0 | Not supported |

## Reporting a vulnerability

請勿在公開 Issue 貼出可利用細節、惡意樣本、憑證或內部文件。

建議使用 GitHub repository 的 **Security → Advisories → New draft security advisory** 私下回報，並提供：

- 受影響版本
- 重現步驟
- 預期與實際結果
- 最小化測試檔案；不得包含真實敏感資料
- 可能影響範圍

## Security boundary

本工具會解析使用者提供的文件。即使採用容器隔離、檔案限制與安全 parser，也不能保證第三方文件 parser 永遠沒有漏洞。正式環境應：

- 定期重建映像並更新基底映像、Python 套件、LibreOffice 與 Tesseract。
- 將 input 來源限制在可信使用者或前置掃毒流程。
- 不將 Docker socket、主機根目錄或敏感目錄掛載進容器。
- 維持 `read_only`、`no-new-privileges`、`cap_drop` 與 CPU/RAM/PID 限制。
- 將 failed/quarantine 文件視為不可信內容。
- 不在日誌中記錄完整文件內容。

更完整的控制項請參考 [`docs/security.md`](docs/security.md)。
