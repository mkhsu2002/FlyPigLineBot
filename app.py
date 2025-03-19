import os
import time
import logging
import traceback
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from flask_login import LoginManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
secret_key = os.environ.get("SESSION_SECRET")
if not secret_key:
    import secrets
    secret_key = secrets.token_hex(16)
    logger.warning("SESSION_SECRET 環境變量未設置，使用隨機生成的密鑰。請在生產環境中設置此環境變量以確保會話一致性。")
app.secret_key = secret_key

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///flypig.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 180,  # 減少連接池回收時間
    "pool_pre_ping": True,
    "pool_size": 10,  # 設置連接池大小
    "max_overflow": 15,  # 設置最大溢出連接數
    "pool_timeout": 30,  # 連接池超時時間
    "connect_args": {"connect_timeout": 10}  # 設置連接超時
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Import and initialize models
import models

# Setup model classes with SQLAlchemy
models.User = type('User', (models.User, db.Model), {})
models.LineUser = type('LineUser', (models.LineUser, db.Model), {})
models.ChatMessage = type('ChatMessage', (models.ChatMessage, db.Model), {})
models.BotStyle = type('BotStyle', (models.BotStyle, db.Model), {})
models.Config = type('Config', (models.Config, db.Model), {})
models.Document = type('Document', (models.Document, db.Model), {})
models.LogEntry = type('LogEntry', (models.LogEntry, db.Model), {})

# Import for easy access
User = models.User
BotStyle = models.BotStyle
Config = models.Config

# Create tables and initialize data
with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Create initial admin user if no users exist
    if not User.query.first():
        from werkzeug.security import generate_password_hash
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin"),
            is_admin=True
        )
        db.session.add(admin)
        
        # Create default bot styles
        default_styles = [
            BotStyle(name="預設", prompt="你是阿昌，和宸清潔庇護工場的代言人，一生奉獻給公益，關懷弱勢，充滿理想與正能量，只用繁體中文聊天，專注陪伴聊天，不碰程式碼或畫圖。", is_default=True),
            BotStyle(name="風趣", prompt="你是一位風趣幽默的阿昌，擅長用輕鬆詼諧的語調回答問題，回應中帶有俏皮的繁體中文表達方式，但不失專業與幫助性。"),
            BotStyle(name="正式", prompt="你是阿昌，一位非常專業的助理，使用正式、商務化的繁體中文進行溝通，提供精確的資訊和適當的建議。"),
            BotStyle(name="專業", prompt="你是阿昌，一位技術專家助理，提供詳細、專業的繁體中文回應，使用特定的技術術語和全面的解釋，讓用戶對技術問題有更深入的理解。"),
        ]
        for style in default_styles:
            db.session.add(style)
        
        # Create default config values
        default_configs = [
            Config(key="OPENAI_TEMPERATURE", value="0.7"),
            Config(key="OPENAI_MAX_TOKENS", value="500"),
            Config(key="LINE_CHANNEL_ID", value=""),
            Config(key="LINE_CHANNEL_SECRET", value=""),
            Config(key="LINE_CHANNEL_ACCESS_TOKEN", value=""),
            Config(key="ACTIVE_BOT_STYLE", value="預設"),
            Config(key="RAG_ENABLED", value="False"),
        ]
        for config in default_configs:
            db.session.add(config)
        
        db.session.commit()
        logger.info("Created initial admin user and default settings")

# Setup login manager
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register blueprints
def register_blueprints():
    # 所有藍圖都使用延遲導入，避免循環引用
    from routes.webhook import webhook_bp
    from routes.auth import auth_bp
    # 註冊 LINE Webhook 處理程序
    from routes.webhook import handle_text_message
    from linebot.models import MessageEvent, TextMessage
    
    # 動態獲取 webhook handler 並註冊事件處理程序
    from routes.webhook import get_line_webhook_handler
    webhook_handler = get_line_webhook_handler()
    webhook_handler.add(MessageEvent, message=TextMessage)(handle_text_message)
    
    # 註冊藍圖
    app.register_blueprint(webhook_bp)
    app.register_blueprint(auth_bp)
    
    # 管理面板藍圖最後註冊，避免循環導入
    try:
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp)
    except ImportError as e:
        logger.error(f"無法導入管理面板藍圖: {e}")

# 註冊藍圖
register_blueprints()

# Create knowledge_base directory if it doesn't exist
if not os.path.exists("knowledge_base"):
    os.makedirs("knowledge_base")
    logger.info("Created knowledge_base directory")

# 檢查關鍵設定是否已配置
def check_critical_settings():
    """檢查關鍵設定是否已正確配置"""
    from routes.utils.config_service import ConfigManager
    
    # 檢查 LINE 相關設定
    line_channel_id = ConfigManager.get("LINE_CHANNEL_ID", "")
    line_channel_secret = ConfigManager.get("LINE_CHANNEL_SECRET", "")
    line_channel_token = ConfigManager.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    
    missing_settings = []
    if not line_channel_id:
        missing_settings.append("LINE_CHANNEL_ID")
    if not line_channel_secret:
        missing_settings.append("LINE_CHANNEL_SECRET")
    if not line_channel_token:
        missing_settings.append("LINE_CHANNEL_ACCESS_TOKEN")
    
    # 檢查 OpenAI API 金鑰
    openai_api_key = ConfigManager.get("OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    if not openai_api_key:
        missing_settings.append("OPENAI_API_KEY")
    
    # 顯示警告
    if missing_settings:
        logger.warning(f"以下關鍵設定尚未配置：{', '.join(missing_settings)}。請在管理後台中設定這些值以確保應用程式正常運行。")
    else:
        logger.info("所有關鍵設定已配置")
        
    # LINE 平台需要 HTTPS 的提醒
    if not os.environ.get("FLASK_ENV") == "development" and not os.environ.get("RUNNING_ON_REPLIT") == "true":
        logger.warning("LINE Messaging API 要求 Webhook URL 必須使用 HTTPS。請確保您的生產環境配置了 SSL/TLS 憑證。")
        logger.info("提示：您可以使用 Let's Encrypt 取得免費的 SSL 憑證，或使用反向代理如 Nginx/Apache 與 Certbot。")

# 在應用程式啟動時執行設定檢查
with app.app_context():
    check_critical_settings()

# 全局錯誤處理器
@app.errorhandler(Exception)
def handle_exception(e):
    """全局異常處理器，捕獲所有未處理的異常"""
    error_id = int(time.time())
    
    # 打印詳細錯誤信息到日誌
    logger.error(f"Unhandled exception [{error_id}]: {str(e)}")
    logger.error(traceback.format_exc())
    
    # 記錄錯誤到數據庫
    try:
        from models import LogEntry
        log_entry = LogEntry(
            level="ERROR",
            message=f"Unhandled exception: {str(e)}",
            module=request.path,
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as log_error:
        logger.error(f"Failed to log error to database: {log_error}")
    
    # 根據請求類型返回不同的響應
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'error': 'Internal Server Error',
            'message': '系統處理請求時發生錯誤，請稍後再試',
            'error_id': error_id
        }), 500
    
    # 對於 webhook 路徑返回 200 OK 避免 LINE 平台重發請求
    if request.path == '/webhook' and request.method == 'POST':
        return 'OK', 200
    
    # 對於普通網頁請求，返回友好的錯誤頁面
    return render_template('error.html', 
                          error_message='處理您的請求時出現了問題',
                          error_id=error_id), 500

# 數據庫錯誤處理器
@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(e):
    """處理數據庫相關錯誤"""
    error_id = int(time.time())
    
    # 打印詳細錯誤信息到日誌
    logger.error(f"Database error [{error_id}]: {str(e)}")
    
    # 回滾事務
    try:
        db.session.rollback()
    except:
        pass
    
    # 根據請求類型返回不同的響應
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'error': 'Database Error',
            'message': '數據庫操作發生錯誤，請稍後再試',
            'error_id': error_id
        }), 500
    
    # 對於 webhook 路徑返回 200 OK 避免 LINE 平台重發請求
    if request.path == '/webhook' and request.method == 'POST':
        return 'OK', 200
    
    # 對於普通網頁請求，返回友好的錯誤頁面
    return render_template('error.html', 
                          error_message='數據庫操作發生錯誤，請稍後再試',
                          error_id=error_id), 500

# 創建自定義的 500 錯誤響應
@app.errorhandler(500)
def internal_server_error(e):
    """自定義 500 錯誤處理"""
    error_id = int(time.time())
    logger.error(f"500 error [{error_id}]: {request.path}")
    
    # 根據請求類型返回不同的響應
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'error': 'Internal Server Error',
            'message': '伺服器內部錯誤，請稍後再試',
            'error_id': error_id
        }), 500
    
    # 對於 webhook 路徑返回 200 OK 避免 LINE 平台重發請求
    if request.path == '/webhook' and request.method == 'POST':
        return 'OK', 200
    
    # 對於普通網頁請求，返回友好的錯誤頁面
    return render_template('error.html', 
                          error_message='伺服器發生內部錯誤，請稍後再試',
                          error_id=error_id), 500

# 自定義 404 錯誤響應
@app.errorhandler(404)
def page_not_found(e):
    """自定義 404 錯誤處理"""
    # 對於 API 請求返回 JSON 格式的錯誤訊息
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'error': 'Not Found',
            'message': '請求的資源不存在'
        }), 404
    
    # 對於普通網頁請求，返回友好的錯誤頁面
    return render_template('error.html', 
                          error_message='找不到您請求的頁面', 
                          error_id=None), 404

logger.info("Application initialization complete")
