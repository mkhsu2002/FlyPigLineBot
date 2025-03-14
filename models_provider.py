"""
Module to provide initialized SQLAlchemy models to avoid circular imports
"""

import logging
from main import db

logger = logging.getLogger(__name__)

def get_model(model_name):
    """
    Get an initialized SQLAlchemy model by name
    
    This function helps avoid circular imports by dynamically importing models
    and binding them to the SQLAlchemy session
    
    Args:
        model_name (str): Name of the model to get
        
    Returns:
        Model class: The requested SQLAlchemy model class
    """
    if model_name == "User":
        from models import User as UserModel
        UserClass = type('User', (UserModel, db.Model), {})
        return UserClass
    
    if model_name == "LineUser":
        from models import LineUser as LineUserModel
        LineUserClass = type('LineUser', (LineUserModel, db.Model), {})
        return LineUserClass
    
    if model_name == "ChatMessage":
        from models import ChatMessage as ChatMessageModel
        ChatMessageClass = type('ChatMessage', (ChatMessageModel, db.Model), {})
        return ChatMessageClass
    
    if model_name == "BotStyle":
        from models import BotStyle as BotStyleModel
        BotStyleClass = type('BotStyle', (BotStyleModel, db.Model), {})
        return BotStyleClass
    
    if model_name == "Config":
        from models import Config as ConfigModel
        ConfigClass = type('Config', (ConfigModel, db.Model), {})
        return ConfigClass
    
    if model_name == "Document":
        from models import Document as DocumentModel
        DocumentClass = type('Document', (DocumentModel, db.Model), {})
        return DocumentClass
        
    if model_name == "LogEntry":
        from models import LogEntry as LogEntryModel
        LogEntryClass = type('LogEntry', (LogEntryModel, db.Model), {})
        return LogEntryClass
    
    logger.error(f"Unknown model name: {model_name}")
    return None