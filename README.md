# FlyPig LINE 聊天機器人 V2.2

FlyPig 是一個基於 Flask 和 OpenAI 的 LINE 聊天機器人，專為「和宸清潔庇護工場」設計，用於關懷弱勢群體和公益活動。機器人具有多種人格風格，並提供完整的管理後台，讓非技術人員也能輕鬆管理和調整機器人行為。

## 🌟 主要特點

- 🤖 多種人格風格設定（貼心、風趣、認真、專業）
- 🧠 整合 OpenAI 的 GPT-4o 大型語言模型
- 📊 強化的管理後台，含即時使用數據統計和詳細消息歷史查詢
- 🛠️ 可自定義機器人的回應風格和提示詞
- 🔒 安全的用戶管理和多層級訪問控制
- 🌐 全面支持繁體中文界面和互動
- 📚 進階知識庫整合 (RAG) 和智能網路搜尋功能
- 🔄 改進的循環引用處理，增強系統穩定性
- 🛡️ 堅固的錯誤處理和資料庫連接管理

## 🔧 技術架構

- **後端**：Flask (Python)
- **數據庫**：SQLite / PostgreSQL
- **AI**：OpenAI GPT-4o
- **消息平台**：LINE Messaging API
- **前端**：Bootstrap + Jinja2 模板
- **向量搜索**：FAISS (Facebook AI Similarity Search)
- **Web 搜索**：SerpAPI 整合

## 📋 安裝與設置

### 前置需求

- Python 3.9+
- OpenAI API 密鑰
- LINE Developers 帳戶和頻道設定
- SerpAPI 密鑰 (選用，用於網路搜尋功能)
- 足夠的記憶體用於向量搜索（推薦至少 1GB RAM）

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

### 5. 知識庫與網路搜尋功能

#### 知識庫 (RAG) 功能
機器人支援 Retrieval Augmented Generation (RAG) 功能，可將自定義的知識文件加入系統，使機器人能夠回答特定領域的問題：

1. 在管理後台的「知識庫」頁面中，上傳 TXT、PDF、DOCX 或 MD 格式的文件
2. 系統會自動處理文件並建立向量索引
3. 啟用 RAG 功能後，機器人回答用戶問題時會參考相關知識
4. 您可以隨時更新、刪除或重建知識庫

#### 網路搜尋功能
機器人支援實時網路搜尋功能，能夠為用戶提供最新的網路資訊：

1. 在「機器人設定」頁面啟用網路搜尋功能
2. 填入 SerpAPI 密鑰（需要先註冊 [SerpAPI](https://serpapi.com/) 獲取）
3. 啟用後，機器人會在適當的時機使用網路搜尋來補充回答

## 🚀 功能詳解

### 1. 管理後台功能

#### 儀表板 (Dashboard)
- **使用統計**：顯示總訊息數、用戶訊息數和機器人回覆數的即時統計
- **最近互動**：列出最近 10 筆用戶與機器人的對話紀錄
- **系統狀態**：顯示 API 連接狀態、活躍風格和功能啟用狀態

#### 機器人設定 (Bot Settings)
- **LINE 頻道設定**：管理 LINE 平台的頻道 ID、密鑰和令牌
- **功能開關**：啟用/停用 RAG 和網路搜尋功能
- **風格選擇**：設定預設風格

#### LLM 設定 (LLM Settings)
- **API 管理**：設定 OpenAI API 密鑰
- **回應調整**：控制溫度參數（創意程度）和最大生成令牌數（回應長度）

#### 機器人風格 (Bot Styles)
- **風格列表**：查看所有可用的風格設定
- **風格創建**：新增自定義風格
- **風格編輯**：修改現有風格的系統提示詞
- **預設風格**：設定系統預設的風格

#### 訊息歷史 (Message History)
- **完整對話紀錄**：查看所有用戶與機器人的對話歷史
- **訊息篩選**：根據用戶 ID 或訊息內容篩選

#### 知識庫管理 (Knowledge Base)
- **檔案上傳**：支援多種格式的知識文件上傳
- **檔案管理**：查看、編輯和刪除知識庫中的文件
- **索引重建**：重新生成向量索引
- **批量上傳**：同時上傳多個檔案

#### 用戶管理 (User Management)
- **用戶列表**：查看所有管理員用戶
- **用戶創建**：新增管理員用戶
- **權限管理**：設定用戶的管理權限

### 2. LINE 機器人功能

#### 基本對話
- **自然語言對話**：基於 GPT-4o 的自然流暢對話能力
- **風格適應**：按照設定的風格調整回覆語氣和內容

#### 特殊指令
- **/style [風格名]**：臨時切換風格
- **/搜尋 [關鍵字]** 或 **/search [關鍵字]**：觸發網路搜尋

#### 知識增強
- **RAG 功能**：從知識庫檢索相關資訊融入回答
- **網路搜尋**：從網路獲取最新資訊

### 3. 系統架構特點

#### 模型提供者架構
- **models_provider.py**：集中管理模型載入，避免循環引用
- **延遲引用**：按需加載模型，提升啟動速度和穩定性

#### 強化錯誤處理
- **全局錯誤捕獲**：集中處理所有異常情況
- **優雅回退機制**：服務中斷時提供友好回應
- **日誌記錄**：詳細記錄系統運行狀態和錯誤

#### 資料庫連接優化
- **連接池管理**：優化數據庫連接效率
- **事務保護**：防止數據損壞
- **自動重連**：處理網絡問題

## 📄 檔案結構說明

- **main.py**: 主程式入口，包含核心路由和模型定義
- **models_provider.py**: 模型提供者，解決循環引用問題
- **services/llm_service.py**: OpenAI 服務和機器人風格處理
- **routes/**: 路由和 API 處理
  - **admin.py**: 管理後台路由
  - **auth.py**: 用戶認證路由
  - **webhook.py**: LINE webhook 處理
- **rag_service.py**: 知識庫和向量搜索實現
- **web_search_service.py**: 網路搜尋服務實現
- **static/**: CSS、JS 和其他靜態文件
- **templates/**: HTML 模板文件
- **models.py**: 數據庫模型定義

## 🔐 資安考量

- 密碼存儲使用 Werkzeug 的 `generate_password_hash` 和 `check_password_hash`
- API 密鑰存儲在數據庫中，並使用環境變量作為優先
- 所有表單請求包含 CSRF 防護
- 敏感操作需要管理員權限

## 📜 授權條款

本項目採用 MIT 授權條款。請遵守 OpenAI 和 LINE 的服務條款。

```
MIT License

Copyright (c) 2025 FlyPig AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👥 貢獻與支持

如果您有任何問題或建議，請提交 Issue 或 Pull Request。

---

## 📋 版本歷史

### V2.2.0 (2025年3月14日)
- 🔄 解決了循環引用問題，大幅提升系統穩定性
- 🧩 實現了模型提供者架構 (models_provider.py)
- 📊 改進了模組組織，分離 routes 和 services
- 🛡️ 增強了錯誤處理和日誌記錄機制
- 🔌 優化了 LINE Webhook 處理流程
- 📝 更新並擴充文檔內容

### V2.0.0 (2025年3月6日)
- 🚀 初始穩定版本發布
- 🤖 多種機器人風格設定
- 🧠 OpenAI GPT-4o 整合
- 📊 完整管理後台功能

---

開發者：FlyPig AI  
版本：2.2.0  
最後更新：2025年3月14日