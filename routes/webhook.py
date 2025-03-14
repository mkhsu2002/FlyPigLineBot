import json
import logging
import os
from flask import Blueprint, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
# 避免循環導入，使用函數延遲導入
from llm_service import LLMService
# 避免循環導入
# from rag_service import RAGService
from web_search_service import WebSearchService
from routes.utils.config_service import get_line_config

# 創建藍圖
webhook_bp = Blueprint('webhook', __name__)
logger = logging.getLogger(__name__)

# 延遲導入數據庫會話
def get_db():
    from app import db
    return db

# 延遲導入模型
def get_models():
    """延遲導入模型以避免循環引用"""
    from app import BotStyle, LineUser, ChatMessage, User, Document
    return BotStyle, LineUser, ChatMessage, User, Document

# Initialize the LINE Bot API and handler
def get_line_bot_api():
    """Get a LINE Bot API instance with current config"""
    config = get_line_config()
    return LineBotApi(config['channel_access_token'])

def get_line_webhook_handler():
    """Get a LINE Webhook handler with current config"""
    config = get_line_config()
    return WebhookHandler(config['channel_secret'])

# LINE Bot webhook route
@webhook_bp.route('/webhook', methods=['POST'])
def line_webhook():
    """Handle LINE webhook events"""
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # Get request body as text
    body = request.get_data(as_text=True)
    
    # Log the request
    logger.info("Request body: %s", body)
    
    # Initialize the webhook handler
    handler = get_line_webhook_handler()
    
    try:
        # Handle the webhook
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Check your channel secret.")
        abort(400)
    
    return 'OK'

# 預先定義處理函數，稍後再註冊到處理程序
def handle_text_message(event):
    """Handle text messages from LINE users"""
    # 設置重試機制參數
    max_db_retries = 3
    db_retry_delay = 0.5  # 初始延遲秒數
    
    try:
        # 獲取消息內容
        user_id = event.source.user_id
        user_message = event.message.text
        logger.info(f"Received message from {user_id}: {user_message[:50]}...")
        
        # 使用重試機制處理數據庫操作
        for db_attempt in range(max_db_retries):
            try:
                # 獲取模型
                _, LineUser, ChatMessage, _, _ = get_models()
                
                # 獲取或創建 LINE 用戶
                line_user = LineUser.query.filter_by(line_user_id=user_id).first()
                if not line_user:
                    # 初始化 LINE Bot API
                    line_bot_api = get_line_bot_api()
                    
                    try:
                        # 從 LINE 獲取用戶資料
                        profile = line_bot_api.get_profile(user_id)
                        line_user = LineUser(
                            line_user_id=user_id,
                            display_name=profile.display_name,
                            picture_url=profile.picture_url,
                            status_message=profile.status_message
                        )
                    except Exception as e:
                        logger.error(f"Error getting user profile: {e}")
                        # 創建一個最小用戶記錄
                        line_user = LineUser(line_user_id=user_id)
                    
                    # 獲取數據庫會話
                    db = get_db()
                    db.session.add(line_user)
                    db.session.commit()
                
                # 記錄用戶訊息到數據庫
                chat_message = ChatMessage(
                    line_user_id=user_id,
                    is_user_message=True,
                    message_text=user_message
                )
                # 獲取數據庫會話（如果尚未獲取）
                db = get_db()
                db.session.add(chat_message)
                db.session.commit()
                break  # 成功後退出重試循環
            except Exception as db_error:
                logger.error(f"Database error (attempt {db_attempt+1}/{max_db_retries}): {db_error}")
                # 獲取數據庫會話並回滾
                db = get_db()
                db.session.rollback()  # 回滾事務
                
                if db_attempt < max_db_retries - 1:
                    # 如果還有重試機會，等待後重試
                    import time
                    time.sleep(db_retry_delay)
                    db_retry_delay *= 2  # 指數退避
                else:
                    # 所有數據庫重試都失敗，記錄錯誤但繼續嘗試回覆
                    logger.error(f"All database retries failed for user {user_id}")
        
        # 檢查風格命令
        bot_style = None
        if user_message.startswith('/style '):
            try:
                style_name = user_message[7:].strip()
                # 設置用戶首選風格
                line_user.active_style = style_name
                # 獲取數據庫會話（如果尚未獲取）
                db = get_db()
                db.session.commit()
                
                response_text = f"風格設定為: {style_name}"
                
                # 保存機器人回應到數據庫
                # 確保已經獲取了模型
                _, _, ChatMessage, _, _ = get_models()
                bot_message = ChatMessage(
                    line_user_id=user_id,
                    is_user_message=False,
                    message_text=response_text,
                    bot_style=style_name
                )
                # 獲取數據庫會話（如果尚未獲取）
                db = get_db()
                db.session.add(bot_message)
                db.session.commit()
                
                # 發送回應
                line_bot_api = get_line_bot_api()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response_text)
                )
                return
            except Exception as style_error:
                logger.error(f"Error processing style command: {style_error}")
                # 獲取數據庫會話並回滾
                db = get_db()
                db.session.rollback()
                response_text = "很抱歉，設定風格時出現問題，請稍後再試。"
        
        # 檢查搜尋命令
        elif user_message.startswith('/搜尋 ') or user_message.startswith('/search '):
            try:
                # 提取搜尋查詢
                if user_message.startswith('/搜尋 '):
                    search_query = user_message[4:].strip()
                else:
                    search_query = user_message[8:].strip()
                    
                if not search_query:
                    response_text = "請提供搜尋關鍵詞，例如：/搜尋 台北天氣"
                else:
                    logger.info(f"Web search requested: {search_query}")
                    # 使用網絡搜尋服務
                    search_response = WebSearchService.answer_with_web_search(search_query)
                    if search_response:
                        response_text = search_response
                    else:
                        response_text = "很抱歉，搜尋功能暫時無法使用或未找到相關資訊。"
            except Exception as search_error:
                logger.error(f"Error processing search command: {search_error}")
                response_text = "很抱歉，搜尋時出現問題，請稍後再試。"
        
        # 常規消息處理
        else:
            try:
                # 如果启用了 RAG，获取上下文
                rag_context = None
                try:
                    # 動態導入 RAGService 避免循環導入
                    from rag_service import RAGService
                    rag_context = RAGService.get_context_for_query(user_message)
                except Exception as rag_error:
                    logger.error(f"Error getting RAG context: {rag_error}")
                
                # 使用用戶的首選風格（如果已設置）
                if hasattr(line_user, 'active_style') and line_user.active_style:
                    bot_style = line_user.active_style
                
                # 使用 OpenAI 生成回應
                response_text = LLMService.generate_response(user_message, bot_style, rag_context)
            except Exception as llm_error:
                logger.error(f"Error generating response: {llm_error}")
                response_text = "很抱歉，生成回應時出現問題，請稍後再試。"
        
        # 保存機器人回應到數據庫
        try:
            # 確保已經獲取了模型
            _, _, ChatMessage, _, _ = get_models()
            bot_message = ChatMessage(
                line_user_id=user_id,
                is_user_message=False,
                message_text=response_text,
                bot_style=bot_style
            )
            # 獲取數據庫會話（如果尚未獲取）
            db = get_db()
            db.session.add(bot_message)
            db.session.commit()
        except Exception as db_save_error:
            logger.error(f"Error saving bot response to database: {db_save_error}")
            # 獲取數據庫會話並回滾
            db = get_db()
            db.session.rollback()
            # 繼續發送回應，即使無法保存到數據庫
        
        # 發送回應
        try:
            line_bot_api = get_line_bot_api()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response_text)
            )
            logger.info(f"Successfully sent response to {user_id}")
        except Exception as reply_error:
            logger.error(f"Error sending response: {reply_error}")
            # 這裡我們無法重試，因為 LINE 的 reply token 只能使用一次
            
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {e}")
        # 嘗試發送錯誤訊息
        try:
            line_bot_api = get_line_bot_api()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="很抱歉，處理您的訊息時出現了問題。")
            )
        except Exception as final_error:
            logger.error(f"Failed to send error message: {final_error}")
            # 此時已無法進一步處理

# Webhook verification endpoint
@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify the webhook URL for LINE Platform"""
    return 'Webhook OK'
