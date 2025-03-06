from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

# These models will be initialized with the actual db instance in app.py
# to avoid circular imports

class User(UserMixin):
    """User model for authentication and admin panel access"""
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LineUser:
    """Model to store LINE user information"""
    __tablename__ = 'line_user'
    
    id = Column(Integer, primary_key=True)
    line_user_id = Column(String(64), unique=True, nullable=False)
    display_name = Column(String(64), nullable=True)
    picture_url = Column(String(256), nullable=True)
    status_message = Column(String(256), nullable=True)
    active_style = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LineUser {self.line_user_id}>'

class ChatMessage:
    """Model to store chat message history"""
    __tablename__ = 'chat_message'
    
    id = Column(Integer, primary_key=True)
    line_user_id = Column(String(64), nullable=False)
    is_user_message = Column(Boolean, default=True)
    message_text = Column(Text, nullable=False)
    bot_style = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'

class BotStyle:
    """Model to store different bot response styles"""
    __tablename__ = 'bot_style'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    prompt = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BotStyle {self.name}>'

class Config:
    """Model to store configuration values"""
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    
    def __repr__(self):
        return f'<Config {self.key}>'

class Document:
    """Model to store knowledge base documents for RAG"""
    __tablename__ = 'document'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    filename = Column(String(128), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<Document {self.title}>'

class LogEntry:
    """Model to store system logs"""
    __tablename__ = 'log_entry'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LogEntry {self.id}>'