from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.models import User
from werkzeug.security import check_password_hash

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email_input = request.form.get('email')
        password = request.form.get('password')
        users = User.query.all()
        user = next((u for u in users if u.email == email_input), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.index'))
        else:
            flash('Невірний email або пароль', 'danger')
            
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    from flask import session
    session.clear() 
    flash('Ви вийшли з системи', 'info')
    return redirect(url_for('main.index'))