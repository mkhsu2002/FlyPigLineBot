# FlyPig LINE 聊天機器人

FlyPig 是一個基於 Flask 和 OpenAI 的 LINE 聊天機器人，專為「和宸清潔庇護工場」設計，用於關懷弱勢群體和公益活動。機器人具有多種人格風格，並提供完整的管理後台，讓非技術人員也能輕鬆管理和調整機器人行為。

## 🌟 主要特點

- 🤖 多種人格風格設定（貼心、風趣、認真、專業）
- 🧠 整合 OpenAI 的 GPT-4o 大型語言模型
- 📊 管理後台含使用數據統計和消息歷史查詢
- 🛠️ 可自定義機器人的回應風格和提示詞
- 🔒 安全的用戶管理和訪問控制
- 🌐 支持繁體中文界面和互動

## 🔧 技術架構

- **後端**：Flask (Python)
- **數據庫**：SQLite / PostgreSQL
- **AI**：OpenAI GPT-4o
- **消息平台**：LINE Messaging API
- **前端**：Bootstrap + Jinja2 模板

## 📋 安裝與設置

### 前置需求

- Python 3.9+
- OpenAI API 密鑰
- LINE Developers 帳戶和頻道設定

### 安裝步驟

1. 克隆此存儲庫：
   ```bash
   git clone https://github.com/yourusername/flypig-line-bot.git
   cd flypig-line-bot
   ```

2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

3. 設置環境變量 (或創建 `.env` 文件)：
   ```
   OPENAI_API_KEY=your_openai_api_key
   SESSION_SECRET=your_session_secret_key
   ```

4. 啟動服務：
   ```bash
   python main.py
   ```
   
5. 訪問管理後台：
   ```
   http://localhost:5000
   ```
   預設管理員帳號：admin / 密碼：admin

## 🔄 自定義為其他 LINE BOT 角色

若要將此機器人調整為其他角色，您需要修改以下設定：

### 1. 機器人人格設定

在管理後台的「機器人風格」頁面中，您可以修改或新增風格。預設有四種風格：

- **貼心**（默認）：關懷輔導型
- **風趣**：幽默風趣型
- **認真**：正式商務型
- **專業**：技術專家型

每種風格都有對應的「系統提示詞」(System Prompt)，定義了機器人的行為和語調。您可以根據需要修改這些提示詞，或創建新的風格。

### 2. 修改程式碼中的預設值

如果要完全更換角色設定，請修改以下檔案：

#### main.py 

找到 `default_styles` 部分（約第 215 行），修改風格名稱和提示詞：

```python
default_styles = [
    BotStyle(name="[新風格名]", prompt="[新角色描述]", is_default=True),
    # ... 其他風格
]
```

#### services/llm_service.py

在 `get_bot_style` 方法中，更新預設風格的設定（約第 30-45 行）。

### 3. LINE 平台設定

1. 登入 [LINE Developers Console](https://developers.line.biz/)
2. 創建一個新的 Provider（若還沒有）
3. 創建一個 Messaging API 頻道
4. 獲取頻道 ID、頻道密鑰和頻道訪問令牌
5. 在 Webhook URL 欄位設置您的 webhook URL：`https://您的網域/webhook`
6. 在管理後台的「LINE機器人設定」頁面中填入以上資訊

### 4. OpenAI API 設定

在管理後台的「LLM 設定」頁面中，填入您的 OpenAI API 密鑰。您也可以調整溫度和最大生成令牌數，以控制回應的創意性和長度。

## 📄 自訂檔案說明

- **main.py**: 主程式入口，包含基本路由和模型定義
- **services/llm_service.py**: OpenAI 服務和機器人風格處理
- **routes/**: 路由和 API 處理（admin.py, auth.py, webhook.py）
- **static/**: CSS、JS 和其他靜態文件
- **templates/**: HTML 模板文件
- **models.py**: 數據庫模型定義

## 🔐 資安考量

- 密碼存儲使用 Werkzeug 的 `generate_password_hash` 和 `check_password_hash`
- API 密鑰存儲在數據庫中，並使用環境變量作為優先
- 所有表單請求包含 CSRF 防護
- 敏感操作需要管理員權限

## 📜 授權條款

本項目僅供學習和研究使用。請遵守 OpenAI 和 LINE 的服務條款。

## 👥 貢獻與支持

如果您有任何問題或建議，請提交 Issue 或 Pull Request。

---

開發者：[您的名字]  
版本：1.0.0  
最後更新：2025年3月