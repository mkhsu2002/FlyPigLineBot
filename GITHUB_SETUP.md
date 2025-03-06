# GitHub 設置指南

以下是將此項目推送到 GitHub 的步驟：

## 1. 初始化 Git 儲存庫

```bash
git init
```

## 2. 添加所有文件

```bash
git add .
```

## 3. 提交初始化

```bash
git commit -m "初始提交：FlyPig LINE Bot"
```

## 4. 連接到 GitHub 存儲庫

首先，在 GitHub 上創建一個新的儲存庫，不要初始化它。

然後，將本地存儲庫連接到 GitHub：

```bash
git remote add origin https://github.com/您的用戶名/flypig-line-bot.git
```

## 5. 推送到 GitHub

```bash
git push -u origin main
```

如果您使用的是 `master` 分支（舊版 Git 默認），請使用：

```bash
git push -u origin master
```

## 6. 保護敏感數據

確保以下敏感數據不會被提交到 GitHub：

- `.env` 文件（包含 API 密鑰）
- 任何數據庫文件（*.db）
- 日誌文件和臨時文件

這些文件應該列在 `.gitignore` 中，已經為您設置好了。

## 7. 設置 GitHub Pages（可選）

如果您想為您的項目創建一個簡單的網站，可以設置 GitHub Pages：

1. 在您的儲存庫中，轉到 Settings > Pages
2. 在 Source 部分，選擇 main 分支和 /(root) 文件夾
3. 點擊 Save

## 8. 設置問題和拉取請求模板（可選）

為了更好地管理貢獻，您可以創建：

- `.github/ISSUE_TEMPLATE/` 目錄，包含問題模板
- `.github/PULL_REQUEST_TEMPLATE.md` 文件，用於拉取請求

## 9. 設置 Actions（可選）

如果您想設置持續集成/持續部署（CI/CD），可以在 `.github/workflows/` 目錄中創建 GitHub Actions 工作流程文件。