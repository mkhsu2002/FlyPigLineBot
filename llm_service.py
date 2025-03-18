import os
import json
import logging
from openai import OpenAI
from routes.utils.config_service import ConfigManager, get_openai_api_key, get_llm_settings
import models
# 避免循環導入問題
from flask import current_app

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with OpenAI LLM"""
    
    @staticmethod
    def get_client():
        """Get an OpenAI client instance with the current API key"""
        api_key = get_openai_api_key()
        if not api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        return OpenAI(api_key=api_key)
    
    @staticmethod
    def get_bot_style(style_name=None):
        """Get the bot style prompt by name or use the active style"""
        if not style_name:
            style_name = ConfigManager.get("ACTIVE_BOT_STYLE", "預設")
        
        style = models.BotStyle.query.filter_by(name=style_name).first()
        if not style:
            # Fallback to default style
            style = models.BotStyle.query.filter_by(name="預設").first()
            
            # If no default style exists, create it
            if not style:
                style = models.BotStyle(
                    name="預設",
                    prompt="你是小艾，一位充滿溫暖與關懷的朋友。你的語氣柔和、貼心，總是耐心傾聽，並以鼓勵與安慰的方式回答問題。你關心對方的情緒，並在回應中帶入支持與正能量。",
                    is_default=True
                )
                from app import db
                db.session.add(style)
                db.session.commit()
        
        return style
    
    @staticmethod
    def generate_response(user_message, style_name=None, rag_context=None):
        """Generate a response using the OpenAI API with the specified style"""
        client = LLMService.get_client()
        if not client:
            return "抱歉，無法連接 AI 服務，請檢查 API 設定。"
        
        # Get the bot style
        style = LLMService.get_bot_style(style_name)
        
        # Get OpenAI settings
        settings = get_llm_settings()
        
        # Build the messages
        messages = [
            {"role": "system", "content": style.prompt}
        ]
        
        # Add RAG context if available
        if rag_context:
            messages.append({
                "role": "system", 
                "content": f"Here is some additional context that might be helpful: {rag_context}"
            })
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=settings["temperature"],
                max_tokens=settings["max_tokens"]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"抱歉，生成回應時發生錯誤：{str(e)}"
    
    @staticmethod
    def validate_api_key(api_key):
        """Validate that the provided OpenAI API key works"""
        try:
            client = OpenAI(api_key=api_key)
            # Make a small request to validate the key
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True, "API key is valid"
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False, f"API key validation failed: {str(e)}"
