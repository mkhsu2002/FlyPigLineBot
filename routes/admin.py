import os
import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import BotStyle, Config, ChatMessage, Document, LineUser, User
from forms import LLMSettingsForm, BotStyleForm, BotSettingsForm, DocumentForm, UserForm, BulkUploadForm
from routes.utils.config_service import ConfigManager

# 創建藍圖但不直接導入可能導致循環引用的模塊
admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# 使用延遲導入避免循環引用問題
def get_db():
    from app import db
    return db

def get_models():
    """延遲導入模型以避免循環引用"""
    # 這些導入已經在頂部完成，但我們仍需此函數來保持一致性
    return BotStyle, LineUser, ChatMessage, User, Document

def get_llm_service():
    """延遲導入LLM服務以避免循環引用"""
    from services.llm_service import LLMService
    return LLMService

def get_rag_service():
    """延遲導入RAG服務以避免循環引用"""
    from rag_service import RAGService
    return RAGService

# Admin access decorator
def admin_required(f):
    """Decorator to require admin access for a route"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required for this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

# Dashboard
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard displaying system overview"""
    # Get stats
    user_count = LineUser.query.count()
    message_count = ChatMessage.query.count()
    document_count = Document.query.count()
    
    # Get recent messages
    recent_messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(10).all()
    
    # Get active style
    active_style_name = ConfigManager.get("ACTIVE_BOT_STYLE", "Default")
    active_style = BotStyle.query.filter_by(name=active_style_name).first()
    
    # Get OpenAI API key status
    openai_key = ConfigManager.get("OPENAI_API_KEY", "")
    api_status = "Configured" if openai_key else "Not Configured"
    
    # Get RAG status
    rag_enabled = ConfigManager.get("RAG_ENABLED", "True") == "True"
    
    return render_template(
        'dashboard.html',
        user_count=user_count,
        message_count=message_count,
        document_count=document_count,
        recent_messages=recent_messages,
        active_style=active_style,
        api_status=api_status,
        rag_enabled=rag_enabled
    )

# LLM Settings
@admin_bp.route('/llm_settings', methods=['GET', 'POST'])
@admin_required
def llm_settings():
    """LLM settings configuration page"""
    form = LLMSettingsForm()
    
    # Pre-fill form with current settings
    if request.method == 'GET':
        form.api_key.data = ConfigManager.get("OPENAI_API_KEY", "")
        form.temperature.data = float(ConfigManager.get("OPENAI_TEMPERATURE", "0.7"))
        form.max_tokens.data = int(ConfigManager.get("OPENAI_MAX_TOKENS", "500"))
    
    # Process form submission
    if form.validate_on_submit():
        # 取得 LLM 服務並驗證 API 密鑰
        LLMService = get_llm_service()
        valid, message = LLMService.validate_api_key(form.api_key.data)
        
        if valid:
            # Save settings
            ConfigManager.set("OPENAI_API_KEY", form.api_key.data)
            ConfigManager.set("OPENAI_TEMPERATURE", str(form.temperature.data))
            ConfigManager.set("OPENAI_MAX_TOKENS", str(form.max_tokens.data))
            
            flash('LLM settings updated successfully.', 'success')
            return redirect(url_for('admin.llm_settings'))
        else:
            flash(f'API key validation failed: {message}', 'danger')
    
    return render_template('llm_settings.html', form=form)

# Bot Settings
@admin_bp.route('/bot_settings', methods=['GET', 'POST'])
@admin_required
def bot_settings():
    """LINE Bot settings configuration page"""
    form = BotSettingsForm()
    
    # Get all available styles for the dropdown
    styles = BotStyle.query.all()
    form.active_style.choices = [(style.name, style.name) for style in styles]
    
    # Pre-fill form with current settings
    if request.method == 'GET':
        form.channel_id.data = ConfigManager.get("LINE_CHANNEL_ID", "2007002420")
        form.channel_secret.data = ConfigManager.get("LINE_CHANNEL_SECRET", "68de5af41837af7d0cf8998774f5dc04")
        form.channel_access_token.data = ConfigManager.get("LINE_CHANNEL_ACCESS_TOKEN", "VaPdPpIRKyOT8VQHAu3bt/KfCy4pJmLL0O76mv5NTtakPiDrDDEyXLPiNqvldZJlMUnLSJ+sWhNpdXgXpm7SiB4bHVJFbnagaftL6IX3PGz7n/msUBX//L2s/OvuLaNcfTMA1a20CuwIzgoGjiTzMgdB04t89/1O/w1cDnyilFU=")
        form.active_style.data = ConfigManager.get("ACTIVE_BOT_STYLE", "Default")
        form.rag_enabled.data = ConfigManager.get("RAG_ENABLED", "True") == "True"
        form.web_search_enabled.data = ConfigManager.get("WEB_SEARCH_ENABLED", "False") == "True"
        form.serpapi_key.data = ConfigManager.get("SERPAPI_KEY", "")
    
    # Process form submission
    if form.validate_on_submit():
        # Save settings
        ConfigManager.set("LINE_CHANNEL_ID", form.channel_id.data)
        ConfigManager.set("LINE_CHANNEL_SECRET", form.channel_secret.data)
        ConfigManager.set("LINE_CHANNEL_ACCESS_TOKEN", form.channel_access_token.data)
        ConfigManager.set("ACTIVE_BOT_STYLE", form.active_style.data)
        ConfigManager.set("RAG_ENABLED", str(form.rag_enabled.data))
        ConfigManager.set("WEB_SEARCH_ENABLED", str(form.web_search_enabled.data))
        ConfigManager.set("SERPAPI_KEY", form.serpapi_key.data)
        
        flash('Bot settings updated successfully.', 'success')
        return redirect(url_for('admin.bot_settings'))
    
    # Get the webhook URL for display
    webhook_url = request.host_url.rstrip('/') + url_for('webhook.line_webhook')
    
    return render_template(
        'bot_settings.html', 
        form=form, 
        webhook_url=webhook_url,
        styles=styles,
        active_style=ConfigManager.get("ACTIVE_BOT_STYLE", "Default"),
        rag_enabled=ConfigManager.get("RAG_ENABLED", "True") == "True",
        web_search_enabled=ConfigManager.get("WEB_SEARCH_ENABLED", "False") == "True",
        serpapi_key=ConfigManager.get("SERPAPI_KEY", "")
    )

# Bot Styles
@admin_bp.route('/bot_styles')
@admin_required
def bot_styles():
    """Bot styles management page"""
    styles = BotStyle.query.all()
    form = BotStyleForm()
    return render_template('bot_styles.html', styles=styles, form=form)

@admin_bp.route('/bot_styles/add', methods=['POST'])
@admin_required
def add_bot_style():
    """Add a new bot style"""
    form = BotStyleForm()
    
    if form.validate_on_submit():
        # Check if style name already exists
        existing = BotStyle.query.filter_by(name=form.name.data).first()
        if existing:
            flash(f'A style with name "{form.name.data}" already exists.', 'danger')
            return redirect(url_for('admin.bot_styles'))
        
        # Create new style
        style = BotStyle(
            name=form.name.data,
            prompt=form.prompt.data,
            description=form.description.data,
            is_default=form.is_default.data
        )
        
        # If this is set as default, update other styles
        if form.is_default.data:
            BotStyle.query.update({'is_default': False})
            ConfigManager.set("ACTIVE_BOT_STYLE", form.name.data)
        
        # 獲取數據庫會話
        db = get_db()
        db.session.add(style)
        db.session.commit()
        
        flash(f'Style "{form.name.data}" added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.bot_styles'))

@admin_bp.route('/bot_styles/edit/<int:style_id>', methods=['POST'])
@admin_required
def edit_bot_style(style_id):
    """Edit an existing bot style"""
    style = BotStyle.query.get_or_404(style_id)
    form = BotStyleForm()
    
    if form.validate_on_submit():
        # Check if renaming to an existing name
        if form.name.data != style.name:
            existing = BotStyle.query.filter_by(name=form.name.data).first()
            if existing:
                flash(f'A style with name "{form.name.data}" already exists.', 'danger')
                return redirect(url_for('admin.bot_styles'))
        
        # Update style
        style.name = form.name.data
        style.prompt = form.prompt.data
        style.description = form.description.data
        
        # Handle default status
        if form.is_default.data and not style.is_default:
            BotStyle.query.update({'is_default': False})
            style.is_default = True
            ConfigManager.set("ACTIVE_BOT_STYLE", form.name.data)
        elif form.is_default.data:
            style.is_default = True
            ConfigManager.set("ACTIVE_BOT_STYLE", form.name.data)
        
        db.session.commit()
        
        flash(f'Style "{form.name.data}" updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.bot_styles'))

@admin_bp.route('/bot_styles/delete/<int:style_id>', methods=['POST'])
@admin_required
def delete_bot_style(style_id):
    """Delete a bot style"""
    style = BotStyle.query.get_or_404(style_id)
    
    # Don't allow deleting the default style
    if style.is_default:
        flash('Cannot delete the default style.', 'danger')
        return redirect(url_for('admin.bot_styles'))
    
    # Check if this is the active style
    if ConfigManager.get("ACTIVE_BOT_STYLE") == style.name:
        # Find a new default style
        default_style = BotStyle.query.filter_by(is_default=True).first()
        if default_style:
            ConfigManager.set("ACTIVE_BOT_STYLE", default_style.name)
        else:
            # If no default, use the first available
            first_style = BotStyle.query.first()
            if first_style:
                ConfigManager.set("ACTIVE_BOT_STYLE", first_style.name)
                first_style.is_default = True
    
    style_name = style.name
    db.session.delete(style)
    db.session.commit()
    
    flash(f'Style "{style_name}" deleted successfully.', 'success')
    return redirect(url_for('admin.bot_styles'))

@admin_bp.route('/bot_styles/get/<int:style_id>')
@admin_required
def get_bot_style(style_id):
    """Get a bot style as JSON for editing"""
    style = BotStyle.query.get_or_404(style_id)
    return jsonify({
        'id': style.id,
        'name': style.name,
        'prompt': style.prompt,
        'description': style.description,
        'is_default': style.is_default
    })

# Message History
@admin_bp.route('/message_history')
@admin_required
def message_history():
    """Message history page"""
    # Get filter parameters
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Build query
    query = ChatMessage.query
    if user_id:
        query = query.filter_by(line_user_id=user_id)
    
    # Get paginated messages
    messages = query.order_by(ChatMessage.timestamp.desc()).paginate(page=page, per_page=per_page)
    
    # Get all LINE users for filter dropdown
    users = LineUser.query.all()
    
    return render_template('message_history.html', messages=messages, users=users, current_user_id=user_id)

@admin_bp.route('/export_messages')
@admin_required
def export_messages():
    """Export message history as CSV or JSON"""
    export_format = request.args.get('format', 'csv').lower()
    user_id = request.args.get('user_id')
    
    # 獲取數據庫會話和模型
    db = get_db()
    ChatMessage, _, _, _, _ = get_models()
    
    # Build query
    query = db.session.query(ChatMessage)
    if user_id:
        query = query.filter_by(line_user_id=user_id)
    
    # Get all messages ordered by timestamp
    messages = query.order_by(ChatMessage.timestamp.asc()).all()
    
    if export_format == 'json':
        # Convert to JSON
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'line_user_id': msg.line_user_id,
                'is_user_message': msg.is_user_message,
                'message_text': msg.message_text,
                'bot_style': msg.bot_style,
                'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Create response
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = 'attachment; filename=messages_export.json'
        return response
    
    # Default to CSV format
    import csv
    import io
    
    # Create CSV content in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'LINE用戶ID', '訊息類型', '訊息內容', '機器人風格', '時間戳記'])
    
    # Write data rows
    for msg in messages:
        writer.writerow([
            msg.id,
            msg.line_user_id,
            '用戶' if msg.is_user_message else '機器人',
            msg.message_text,
            msg.bot_style or '',
            msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create response with CSV content
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=messages_export.csv'
    return response

# Knowledge Base
@admin_bp.route('/knowledge_base')
@admin_required
def knowledge_base():
    """Knowledge base management page"""
    # 獲取數據庫會話和模型
    db = get_db()
    _, _, _, _, Document = get_models()
    
    # 修正查詢方式，從類實例查詢而不是類本身
    # SQLAlchemy 在使用 ORM 模式時需要實例化的模型對象
    from sqlalchemy import desc
    documents = db.session.query(Document).order_by(desc('uploaded_at')).all()
    form = DocumentForm()
    return render_template('knowledge_base.html', documents=documents, form=form)

@admin_bp.route('/knowledge_base/add', methods=['POST'])
@admin_required
def add_document():
    """Add a document to the knowledge base"""
    form = DocumentForm()
    
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        filename = None
        
        # Handle file upload
        if form.file.data:
            # Process file content
            file = form.file.data
            filename = secure_filename(file.filename)
            
            # Read file content
            file_content = file.read().decode('utf-8', errors='replace')
            
            # If no content was provided in the form, use file content
            if not content:
                content = file_content
        
        # Ensure we have content
        if not content:
            flash('文件必須包含內容，可以從文字欄位或上傳檔案獲取', 'danger')
            return redirect(url_for('admin.knowledge_base'))
        
        # 取得 RAG 服務並添加文檔
        RAGService = get_rag_service()
        success, result = RAGService.add_document(title, content, filename)
        
        if success:
            flash(f'文件 "{title}" 添加成功', 'success')
        else:
            flash(f'添加文件錯誤: {result}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.knowledge_base'))
    
@admin_bp.route('/knowledge_base/bulk_upload', methods=['POST'])
@admin_required
def bulk_upload():
    """Bulk upload multiple documents to the knowledge base"""
    # 獲取 RAG 服務
    RAGService = get_rag_service()
    if 'files' not in request.files:
        flash('未選擇任何檔案', 'danger')
        return redirect(url_for('admin.knowledge_base'))
        
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        flash('未選擇任何檔案', 'danger')
        return redirect(url_for('admin.knowledge_base'))
    
    title_prefix = request.form.get('title_prefix', '')
    
    # Allowed file extensions
    allowed_extensions = ['txt', 'pdf', 'docx', 'md']
    
    success_count = 0
    error_count = 0
    
    for file in files:
        # Check if file extension is allowed
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            flash(f'不支援的檔案格式: {file.filename}', 'warning')
            error_count += 1
            continue
            
        try:
            # Create a title from the filename (without extension)
            raw_title = file.filename.rsplit('.', 1)[0]
            # Format title: replace underscore and dash with space, capitalize words
            formatted_title = ' '.join(word.capitalize() for word in raw_title.replace('_', ' ').replace('-', ' ').split())
            title = f"{title_prefix}{formatted_title}" if title_prefix else formatted_title
            
            # Read file content
            content = file.read().decode('utf-8', errors='replace')
            
            if not content.strip():
                flash(f'檔案 {file.filename} 是空的', 'warning')
                error_count += 1
                continue
                
            # Add to database
            success, result = RAGService.add_document(title, content, file.filename)
            
            if success:
                success_count += 1
            else:
                flash(f'添加文件 {file.filename} 錯誤: {result}', 'danger')
                error_count += 1
                
        except Exception as e:
            flash(f'處理檔案 {file.filename} 時發生錯誤: {str(e)}', 'danger')
            error_count += 1
    
    # Show summary
    if success_count > 0:
        flash(f'成功上傳 {success_count} 個文件到知識庫', 'success')
        
    if error_count > 0:
        flash(f'{error_count} 個文件處理失敗', 'warning')
    
    # Rebuild index if any document was added successfully
    if success_count > 0:
        RAGService.update_index()
        
    return redirect(url_for('admin.knowledge_base'))

@admin_bp.route('/knowledge_base/delete/<int:doc_id>', methods=['POST'])
@admin_required
def delete_document(doc_id):
    """Delete a document from the knowledge base"""
    # 獲取 RAG 服務
    RAGService = get_rag_service()
    
    success, message = RAGService.delete_document(doc_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.knowledge_base'))

@admin_bp.route('/knowledge_base/view/<int:doc_id>')
@admin_required
def view_document(doc_id):
    """View a document's content"""
    # 獲取數據庫會話和模型
    db = get_db()
    _, _, _, _, Document = get_models()
    
    document = db.session.query(Document).get_or_404(doc_id)
    return jsonify({
        'id': document.id,
        'title': document.title,
        'content': document.content
    })

@admin_bp.route('/knowledge_base/download/<int:doc_id>')
@admin_required
def download_document(doc_id):
    """Download a document's content as a text file"""
    from flask import Response
    
    # 獲取數據庫會話和模型
    db = get_db()
    _, _, _, _, Document = get_models()
    
    document = db.session.query(Document).get_or_404(doc_id)
    
    # Create a response with the document content
    response = Response(document.content)
    
    # Set the appropriate headers for file download
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename="{document.title}.txt"'
    
    return response

@admin_bp.route('/knowledge_base/rebuild_index', methods=['POST'])
@admin_required
def rebuild_index():
    """Rebuild the FAISS index"""
    # 獲取 RAG 服務
    RAGService = get_rag_service()
    
    success = RAGService.update_index()
    
    if success:
        flash('Knowledge base index rebuilt successfully.', 'success')
    else:
        flash('Error rebuilding knowledge base index.', 'danger')
    
    return redirect(url_for('admin.knowledge_base'))

@admin_bp.route('/knowledge_base/export')
@admin_required
def export_knowledge_base():
    """Export all knowledge base documents as a downloadable file"""
    from flask import Response
    
    # 獲取 RAG 服務
    RAGService = get_rag_service()
    
    # Get exported content
    content = RAGService.export_knowledge_base()
    
    if not content:
        flash('Error exporting knowledge base.', 'danger')
        return redirect(url_for('admin.knowledge_base'))
    
    # Create a response with the document content
    response = Response(content)
    
    # Set the appropriate headers for file download
    response.headers['Content-Type'] = 'text/markdown'
    response.headers['Content-Disposition'] = f'attachment; filename="flypig_knowledge_base_export.md"'
    
    return response

# User Management
@admin_bp.route('/user_management')
@admin_required
def user_management():
    """User management page for admin panel users"""
    # 獲取數據庫會話和模型
    db = get_db()
    User, _, _, _, _ = get_models()
    
    users = db.session.query(User).all()
    form = UserForm()
    return render_template('user_management.html', users=users, form=form)

@admin_bp.route('/user_management/add', methods=['POST'])
@admin_required
def add_user():
    """Add a new admin panel user"""
    # 獲取數據庫會話和模型
    db = get_db()
    User, _, _, _, _ = get_models()
    
    form = UserForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if db.session.query(User).filter_by(username=form.username.data).first():
            flash(f'Username "{form.username.data}" is already taken.', 'danger')
            return redirect(url_for('admin.user_management'))
        
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash(f'Email "{form.email.data}" is already registered.', 'danger')
            return redirect(url_for('admin.user_management'))
        
        # Check for password
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return redirect(url_for('admin.user_management'))
        
        # Create new user
        from werkzeug.security import generate_password_hash
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=form.is_admin.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{form.username.data}" added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/user_management/edit/<int:user_id>', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit an existing admin panel user"""
    # 獲取數據庫會話和模型
    db = get_db()
    User, _, _, _, _ = get_models()
    
    user = db.session.query(User).get_or_404(user_id)
    form = UserForm()
    
    # Don't allow non-admin to edit the last admin
    if user.is_admin and not form.is_admin.data:
        admin_count = db.session.query(User).filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('Cannot remove admin status from the last admin user.', 'danger')
            return redirect(url_for('admin.user_management'))
    
    if form.validate_on_submit():
        # Check username and email uniqueness if changed
        if form.username.data != user.username and db.session.query(User).filter_by(username=form.username.data).first():
            flash(f'Username "{form.username.data}" is already taken.', 'danger')
            return redirect(url_for('admin.user_management'))
        
        if form.email.data != user.email and db.session.query(User).filter_by(email=form.email.data).first():
            flash(f'Email "{form.email.data}" is already registered.', 'danger')
            return redirect(url_for('admin.user_management'))
        
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        # Update password if provided
        if form.password.data:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(form.password.data)
        
        db.session.commit()
        
        flash(f'User "{form.username.data}" updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/user_management/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete an admin panel user"""
    # 獲取數據庫會話和模型
    db = get_db()
    User, _, _, _, _ = get_models()
    
    user = db.session.query(User).get_or_404(user_id)
    
    # Don't allow deleting the last admin
    if user.is_admin:
        admin_count = db.session.query(User).filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('Cannot delete the last admin user.', 'danger')
            return redirect(url_for('admin.user_management'))
    
    # Don't allow deleting self
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.user_management'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" deleted successfully.', 'success')
    return redirect(url_for('admin.user_management'))

@admin_bp.route('/user_management/get/<int:user_id>')
@admin_required
def get_user(user_id):
    """Get a user as JSON for editing"""
    # 獲取數據庫會話和模型
    db = get_db()
    User, _, _, _, _ = get_models()
    
    user = db.session.query(User).get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    })

# 設定匯出和匯入功能
@admin_bp.route('/export_bot_settings')
@admin_required
def export_bot_settings():
    """Export LINE Bot settings as JSON file"""
    settings = {
        'channel_id': ConfigManager.get("LINE_CHANNEL_ID", ""),
        'channel_secret': ConfigManager.get("LINE_CHANNEL_SECRET", ""),
        'channel_access_token': ConfigManager.get("LINE_CHANNEL_ACCESS_TOKEN", ""),
        'active_style': ConfigManager.get("ACTIVE_BOT_STYLE", "Default"),
        'rag_enabled': ConfigManager.get("RAG_ENABLED", "True") == "True",
        'web_search_enabled': ConfigManager.get("WEB_SEARCH_ENABLED", "False") == "True",
        'serpapi_key': ConfigManager.get("SERPAPI_KEY", ""),
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Create response
    response = make_response(json.dumps(settings, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=flypig_bot_settings.json'
    return response

@admin_bp.route('/import_bot_settings', methods=['POST'])
@admin_required
def import_bot_settings():
    """Import LINE Bot settings from JSON file"""
    if 'settings_file' not in request.files:
        flash('未選擇設定檔案', 'danger')
        return redirect(url_for('admin.bot_settings'))
    
    file = request.files['settings_file']
    if file.filename == '':
        flash('未選擇設定檔案', 'danger')
        return redirect(url_for('admin.bot_settings'))
    
    if not file.filename.lower().endswith('.json'):
        flash('僅支援 JSON 檔案格式', 'danger')
        return redirect(url_for('admin.bot_settings'))
    
    try:
        content = file.read().decode('utf-8')
        settings = json.loads(content)
        
        # Validate required fields
        required_fields = ['channel_id', 'channel_secret', 'channel_access_token', 'active_style']
        for field in required_fields:
            if field not in settings:
                flash(f'設定檔案缺少必要欄位: {field}', 'danger')
                return redirect(url_for('admin.bot_settings'))
        
        # Update settings
        ConfigManager.set("LINE_CHANNEL_ID", settings['channel_id'])
        ConfigManager.set("LINE_CHANNEL_SECRET", settings['channel_secret'])
        ConfigManager.set("LINE_CHANNEL_ACCESS_TOKEN", settings['channel_access_token'])
        ConfigManager.set("ACTIVE_BOT_STYLE", settings['active_style'])
        
        # Optional settings
        if 'rag_enabled' in settings:
            ConfigManager.set("RAG_ENABLED", str(settings['rag_enabled']))
        if 'web_search_enabled' in settings:
            ConfigManager.set("WEB_SEARCH_ENABLED", str(settings['web_search_enabled']))
        if 'serpapi_key' in settings:
            ConfigManager.set("SERPAPI_KEY", settings['serpapi_key'])
        
        flash('機器人設定匯入成功', 'success')
    except Exception as e:
        flash(f'匯入設定時發生錯誤: {str(e)}', 'danger')
        logger.error(f"Import bot settings error: {str(e)}")
    
    return redirect(url_for('admin.bot_settings'))

@admin_bp.route('/export_bot_styles')
@admin_required
def export_bot_styles():
    """Export all bot styles as JSON file"""
    # 獲取數據庫會話和模型
    db = get_db()
    BotStyle, _, _, _, _ = get_models()
    
    styles = db.session.query(BotStyle).all()
    export_data = []
    
    for style in styles:
        export_data.append({
            'name': style.name,
            'prompt': style.prompt,
            'description': style.description,
            'is_default': style.is_default
        })
    
    export = {
        'styles': export_data,
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Create response
    response = make_response(json.dumps(export, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=flypig_bot_styles.json'
    return response

@admin_bp.route('/import_bot_styles', methods=['POST'])
@admin_required
def import_bot_styles():
    """Import bot styles from JSON file"""
    # 獲取數據庫會話和模型
    db = get_db()
    BotStyle, _, _, _, _ = get_models()
    
    if 'styles_file' not in request.files:
        flash('未選擇風格檔案', 'danger')
        return redirect(url_for('admin.bot_styles'))
    
    file = request.files['styles_file']
    if file.filename == '':
        flash('未選擇風格檔案', 'danger')
        return redirect(url_for('admin.bot_styles'))
    
    if not file.filename.lower().endswith('.json'):
        flash('僅支援 JSON 檔案格式', 'danger')
        return redirect(url_for('admin.bot_styles'))
    
    # Check if we should overwrite existing styles
    overwrite = 'overwrite_existing' in request.form
    
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        if 'styles' not in data or not isinstance(data['styles'], list):
            flash('檔案格式無效，未找到風格資料', 'danger')
            return redirect(url_for('admin.bot_styles'))
        
        styles_data = data['styles']
        imported_count = 0
        skipped_count = 0
        
        for style_data in styles_data:
            # Validate required fields
            if 'name' not in style_data or 'prompt' not in style_data:
                logger.warning(f"Skipping style import - missing required fields: {style_data}")
                skipped_count += 1
                continue
            
            # Check if style exists
            existing = db.session.query(BotStyle).filter_by(name=style_data['name']).first()
            if existing and not overwrite:
                logger.info(f"Skipping existing style: {style_data['name']}")
                skipped_count += 1
                continue
            
            if existing:
                # Update existing style
                existing.prompt = style_data['prompt']
                existing.description = style_data.get('description', '')
                if 'is_default' in style_data and style_data['is_default']:
                    db.session.query(BotStyle).update({'is_default': False})
                    existing.is_default = True
                    ConfigManager.set("ACTIVE_BOT_STYLE", existing.name)
            else:
                # Create new style
                is_default = style_data.get('is_default', False)
                if is_default:
                    db.session.query(BotStyle).update({'is_default': False})
                    
                new_style = BotStyle(
                    name=style_data['name'],
                    prompt=style_data['prompt'],
                    description=style_data.get('description', ''),
                    is_default=is_default
                )
                db.session.add(new_style)
                
                if is_default:
                    ConfigManager.set("ACTIVE_BOT_STYLE", new_style.name)
            
            imported_count += 1
        
        db.session.commit()
        
        if imported_count > 0:
            if skipped_count > 0:
                flash(f'成功匯入 {imported_count} 個風格，跳過 {skipped_count} 個風格', 'success')
            else:
                flash(f'成功匯入 {imported_count} 個風格', 'success')
        else:
            flash('未匯入任何風格', 'warning')
            
    except Exception as e:
        flash(f'匯入風格時發生錯誤: {str(e)}', 'danger')
        logger.error(f"Import bot styles error: {str(e)}")
    
    return redirect(url_for('admin.bot_styles'))

@admin_bp.route('/export_llm_settings')
@admin_required
def export_llm_settings():
    """Export LLM settings as JSON file"""
    settings = {
        'api_key': ConfigManager.get("OPENAI_API_KEY", ""),
        'temperature': float(ConfigManager.get("OPENAI_TEMPERATURE", "0.7")),
        'max_tokens': int(ConfigManager.get("OPENAI_MAX_TOKENS", "500")),
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Create response
    response = make_response(json.dumps(settings, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = 'attachment; filename=flypig_llm_settings.json'
    return response

@admin_bp.route('/import_llm_settings', methods=['POST'])
@admin_required
def import_llm_settings():
    """Import LLM settings from JSON file"""
    if 'settings_file' not in request.files:
        flash('未選擇設定檔案', 'danger')
        return redirect(url_for('admin.llm_settings'))
    
    file = request.files['settings_file']
    if file.filename == '':
        flash('未選擇設定檔案', 'danger')
        return redirect(url_for('admin.llm_settings'))
    
    if not file.filename.lower().endswith('.json'):
        flash('僅支援 JSON 檔案格式', 'danger')
        return redirect(url_for('admin.llm_settings'))
    
    try:
        content = file.read().decode('utf-8')
        settings = json.loads(content)
        
        # Validate required fields
        required_fields = ['api_key', 'temperature', 'max_tokens']
        for field in required_fields:
            if field not in settings:
                flash(f'設定檔案缺少必要欄位: {field}', 'danger')
                return redirect(url_for('admin.llm_settings'))
        
        # 獲取 LLM 服務並驗證 API key
        LLMService = get_llm_service()
        valid, message = LLMService.validate_api_key(settings['api_key'])
        if not valid:
            flash(f'API 金鑰驗證失敗: {message}', 'danger')
            return redirect(url_for('admin.llm_settings'))
        
        # Update settings
        ConfigManager.set("OPENAI_API_KEY", settings['api_key'])
        ConfigManager.set("OPENAI_TEMPERATURE", str(settings['temperature']))
        ConfigManager.set("OPENAI_MAX_TOKENS", str(settings['max_tokens']))
        
        flash('LLM 設定匯入成功', 'success')
    except Exception as e:
        flash(f'匯入設定時發生錯誤: {str(e)}', 'danger')
        logger.error(f"Import LLM settings error: {str(e)}")
    
    return redirect(url_for('admin.llm_settings'))
