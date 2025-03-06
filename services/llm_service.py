import os
import json
import logging
from openai import OpenAI
from datetime import datetime, timezone, timedelta
from routes.utils.config_service import ConfigManager, get_openai_api_key, get_llm_settings

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
        # Import here to avoid circular imports
        from app import db
        from main import BotStyle
        
        if not style_name:
            style_name = ConfigManager.get("ACTIVE_BOT_STYLE", "貼心")
        
        style = BotStyle.query.filter_by(name=style_name).first()
        if not style:
            # Fallback to default style
            style = BotStyle.query.filter_by(name="貼心").first()
            
            # If no default style exists, create it
            if not style:
                style = BotStyle(
                    name="貼心",
                    prompt="你是小艾，一個親切溫暖的助理，專注於提供友善、善解人意的服務。你只使用繁體中文交流，表現出關懷、同理心和支持。你會耐心聆聽，並給予令人感到被理解與被照顧的回應。",
                    is_default=True
                )
                db.session.add(style)
                db.session.commit()
        
        return style
    
    @staticmethod
    def generate_response(user_message, style_name=None, rag_context=None, system_prompt=None):
        """Generate a response using the OpenAI API with the specified style
        
        Args:
            user_message (str): The user's message to respond to
            style_name (str, optional): The name of the bot style to use. Defaults to None.
            rag_context (str, optional): Additional context from RAG. Defaults to None.
            system_prompt (str, optional): Custom system prompt that overrides the style. Defaults to None.
        """
        client = LLMService.get_client()
        if not client:
            return "抱歉，無法連接 AI 服務，請檢查 API 設定。"
        
        # Get OpenAI settings
        settings = get_llm_settings()
        
        # Get current date and time in Taiwan timezone (UTC+8)
        taiwan_tz = timezone(timedelta(hours=8))
        current_date = datetime.now(taiwan_tz).strftime("%Y年%m月%d日")
        
        # Determine the system prompt
        if system_prompt:
            # Use the provided custom system prompt
            prompt_content = f"{system_prompt} 真實即時日期是 {current_date}。"
        else:
            # Get the bot style
            style = LLMService.get_bot_style(style_name)
            prompt_content = f"{style.prompt} 真實即時日期是 {current_date}。"
        
        # Build the messages with date information
        messages = [
            {"role": "system", "content": prompt_content}
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
            if not api_key:
                return False
                
            client = OpenAI(api_key=api_key)
            # Make a small request to validate the key
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False