import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User
from forms import LoginForm

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Log successful login
            logger.info(f"User {user.username} logged in successfully")
            
            flash(f'Welcome, {user.username}!', 'success')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for username: {form.username.data}")
            
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    username = current_user.username
    logout_user()
    
    # Log logout
    logger.info(f"User {username} logged out")
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
