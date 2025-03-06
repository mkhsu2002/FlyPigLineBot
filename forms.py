from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UserForm(FlaskForm):
    """Form for creating/editing users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    password_confirm = PasswordField(
        'Confirm Password', 
        validators=[
            Optional(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Save')

class LLMSettingsForm(FlaskForm):
    """Form for LLM settings"""
    api_key = StringField('OpenAI API Key', validators=[DataRequired()])
    temperature = FloatField(
        'Temperature', 
        validators=[DataRequired(), NumberRange(min=0, max=2)],
        default=0.7
    )
    max_tokens = IntegerField(
        'Max Tokens', 
        validators=[DataRequired(), NumberRange(min=50, max=4000)],
        default=500
    )
    submit = SubmitField('Save Settings')

class BotStyleForm(FlaskForm):
    """Form for creating/editing bot styles"""
    name = StringField('Style Name', validators=[DataRequired(), Length(min=1, max=64)])
    prompt = TextAreaField('System Prompt', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    is_default = BooleanField('Set as Default')
    submit = SubmitField('Save Style')

class BotSettingsForm(FlaskForm):
    """Form for LINE Bot settings"""
    channel_id = StringField('Channel ID', validators=[DataRequired()])
    channel_secret = StringField('Channel Secret', validators=[DataRequired()])
    channel_access_token = StringField('Channel Access Token', validators=[DataRequired()])
    active_style = SelectField('Active Style', validators=[DataRequired()])
    rag_enabled = BooleanField('Enable RAG (Retrieval Augmented Generation)')
    web_search_enabled = BooleanField('Enable Web Search')
    serpapi_key = StringField('SerpAPI Key', validators=[Optional()])
    submit = SubmitField('Save Settings')

class DocumentForm(FlaskForm):
    """Form for adding documents to the knowledge base"""
    title = StringField('文件標題', validators=[DataRequired()])
    content = TextAreaField('文件內容', validators=[Optional()])
    file = FileField('上傳檔案', validators=[
        Optional(),
        FileAllowed(['txt', 'pdf', 'docx', 'md'], '僅支援文字文件！')
    ])
    submit = SubmitField('添加文件')
    
class BulkUploadForm(FlaskForm):
    """Form for bulk uploading documents to the knowledge base"""
    files = FileField('選擇多個檔案', validators=[
        DataRequired(),
        FileAllowed(['txt', 'pdf', 'docx', 'md'], '僅支援文字文件！')
    ])
    title_prefix = StringField('標題前綴', validators=[Optional()], 
                              description='可選的標題前綴，將加在每個檔案名之前')
    submit = SubmitField('批量上傳')
