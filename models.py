from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """User model for authentication and admin panel access"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LineUser(db.Model):
    """Model to store LINE user information"""
    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(64), nullable=True)
    picture_url = db.Column(db.String(256), nullable=True)
    status_message = db.Column(db.String(256), nullable=True)
    active_style = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LineUser {self.line_user_id}>'

class ChatMessage(db.Model):
    """Model to store chat message history"""
    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(64), nullable=False)
    is_user_message = db.Column(db.Boolean, default=True)
    message_text = db.Column(db.Text, nullable=False)
    bot_style = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'

class BotStyle(db.Model):
    """Model to store different bot response styles"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BotStyle {self.name}>'

class Config(db.Model):
    """Model to store configuration values"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Config {self.key}>'

class Document(db.Model):
    """Model to store knowledge base documents for RAG"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(128), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Document {self.title}>'

class LogEntry(db.Model):
    """Model to store system logs"""
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LogEntry {self.id}>'
