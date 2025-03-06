import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "flypig-line-bot-secret")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///flypig.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Import models
with app.app_context():
    # Import models here to avoid circular imports
    import models
    from models import User, BotStyle, Config
    
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
            BotStyle(name="Default", prompt="You are a helpful assistant. Respond in a straightforward manner."),
            BotStyle(name="Humorous", prompt="You are a funny assistant. Always inject humor into your responses."),
            BotStyle(name="Formal", prompt="You are a formal and professional assistant. Use proper language and avoid colloquialisms."),
            BotStyle(name="Technical", prompt="You are a technical assistant. Provide detailed technical explanations."),
        ]
        for style in default_styles:
            db.session.add(style)
        
        # Create default config values
        default_configs = [
            Config(key="OPENAI_API_KEY", value=""),
            Config(key="OPENAI_TEMPERATURE", value="0.7"),
            Config(key="OPENAI_MAX_TOKENS", value="500"),
            Config(key="LINE_CHANNEL_ID", value="2007002420"),
            Config(key="LINE_CHANNEL_SECRET", value="68de5af41837af7d0cf8998774f5dc04"),
            Config(key="LINE_CHANNEL_ACCESS_TOKEN", value="VaPdPpIRKyOT8VQHAu3bt/KfCy4pJmLL0O76mv5NTtakPiDrDDEyXLPiNqvldZJlMUnLSJ+sWhNpdXgXpm7SiB4bHVJFbnagaftL6IX3PGz7n/msUBX//L2s/OvuLaNcfTMA1a20CuwIzgoGjiTzMgdB04t89/1O/w1cDnyilFU="),
            Config(key="ACTIVE_BOT_STYLE", value="Default"),
            Config(key="RAG_ENABLED", value="True"),
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
from routes.admin import admin_bp
from routes.webhook import webhook_bp
from routes.auth import auth_bp

app.register_blueprint(admin_bp)
app.register_blueprint(webhook_bp)
app.register_blueprint(auth_bp)

# Create knowledge_base directory if it doesn't exist
import os
if not os.path.exists("knowledge_base"):
    os.makedirs("knowledge_base")
    logger.info("Created knowledge_base directory")

logger.info("Application initialization complete")
