# FlyPigLineBotV1 - GitHub 設置指南

這個指南將幫助你從 GitHub 克隆 FlyPigLineBotV1 專案並進行設置和部署。

## 前置條件

在開始之前，請確保你已安裝以下軟體：

1. Python 3.9+ 和 pip
2. Git
3. 適合您平台的數據庫（默認使用 SQLite，無需額外安裝）
4. 註冊 [LINE Developers](https://developers.line.biz/) 帳戶並創建 Messaging API 頻道
5. 註冊 [OpenAI](https://platform.openai.com/signup) 帳戶並獲取 API 密鑰

## 步驟 1：克隆存儲庫

```bash
# 克隆存儲庫
git clone https://github.com/[YOUR_USERNAME]/FlyPigLineBotV1.git

# 進入專案目錄
cd FlyPigLineBotV1
```

## 步驟 2：設置虛擬環境和安裝依賴

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# 在 Windows 上:
venv\Scripts\activate
# 在 macOS/Linux 上:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

## 步驟 3：設置環境變量

創建 `.env` 文件並添加以下內容：

```
# 必需的配置
OPENAI_API_KEY=你的_OpenAI_API_密鑰
SESSION_SECRET=任意複雜的隨機字符串

# 可選配置（也可以在管理後台設置）
# LINE_CHANNEL_ID=你的_LINE_頻道_ID
# LINE_CHANNEL_SECRET=你的_LINE_頻道密鑰
# LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_頻道訪問令牌
# SERPAPI_KEY=你的_SerpAPI_密鑰（如果需要網路搜尋功能）
# FLASK_ENV=development（開發環境設置）
```

## 步驟 4：初始化資料庫並啟動應用

```bash
# 啟動應用（會自動創建資料庫和初始用戶）
python app.py
```

初次啟動時會自動：
- 創建資料庫
- 創建默認管理員帳戶（用戶名：admin，密碼：admin）
- 初始化默認機器人風格

## 步驟 5：訪問管理後台

在瀏覽器中打開 [http://localhost:5000](http://localhost:5000)
使用默認管理員帳戶登入：
- 用戶名：admin
- 密碼：admin

**重要：** 首次登入後請立即變更默認密碼！

## 步驟 6：配置 FlyPigLineBotV1 設定

1. 在管理後台中，前往「LINE 機器人設定」頁面
2. 輸入您的 LINE 頻道 ID、頻道密鑰和頻道訪問令牌
3. 複製顯示的 Webhook URL
4. 前往 [LINE Developers Console](https://developers.line.biz/)
5. 在您的 Messaging API 頻道設定中，粘貼 Webhook URL 並啟用 webhook

## 步驟 7：配置 OpenAI API 設定

1. 在管理後台中，前往「LLM 設定」頁面
2. 輸入您的 OpenAI API 密鑰
3. 調整溫度和最大令牌數（根據需要）

## 生產環境部署

### 選項 1：使用 Gunicorn 和 Nginx（推薦用於 Linux 服務器）

```bash
# 安裝 gunicorn
pip install gunicorn

# 啟動 gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

然後設置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 選項 2：使用 Heroku

1. 創建 `Procfile` 文件：
   ```
   web: gunicorn app:app
   ```

2. 部署到 Heroku：
   ```bash
   heroku create
   git push heroku main
   ```

### 選項 3：使用 Replit

1. 將代碼上傳到您的 Replit 項目
2. 添加環境變量到 Replit 密鑰存儲中
3. 使用 Replit 的 `.replit` 文件設置啟動命令：
   ```
   run = "python app.py"
   ```

## 注意事項

1. **安全考慮:** 在生產環境中，請務必：
   - 更改默認管理員密碼
   - 使用強密鑰作為 SESSION_SECRET
   - 確保敏感配置儲存在環境變量中，而不是硬編碼
   - 使用 HTTPS 保護所有流量

2. **LINE Webhook 要求 HTTPS:** LINE Messaging API 要求 Webhook URL 必須使用 HTTPS。在生產環境中，您需要配置 SSL/TLS 證書，可以使用：
   - Let's Encrypt 免費證書
   - Nginx 或 Apache 配置 SSL
   - 或使用 Heroku、Replit、Vercel 等提供 HTTPS 的服務

3. **數據庫考慮:** 默認使用 SQLite，適合小規模使用。對於生產環境，考慮使用：
   - PostgreSQL（推薦）
   - MySQL
   
   修改 `DATABASE_URL` 環境變量以切換數據庫。

## 故障排除

如果遇到問題，請檢查：

1. 日誌文件以查看詳細錯誤信息
2. 確保所有環境變量正確設置
3. 確保 LINE Webhook URL 能夠被外部訪問且使用 HTTPS
4. 檢查 OpenAI API 密鑰是否有效且有足夠的餘額

如需更多幫助，請在 GitHub 上提交 Issue。