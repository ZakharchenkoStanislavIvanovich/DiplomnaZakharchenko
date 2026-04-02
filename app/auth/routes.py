from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.models import User
from werkzeug.security import check_password_hash
from app.auth.forms import LoginForm  # Форма вже імпортована

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Якщо користувач уже залогінений — відправляємо на головну
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # 2. Створюємо об'єкт форми
    form = LoginForm()
    
    # 3. validate_on_submit() автоматично перевіряє POST-запит та CSRF-токен
    if form.validate_on_submit():
        # Отримуємо всіх користувачів (база поверне їх, а @property розшифрує)
        users = User.query.all()
        # Шукаємо того, чий розшифрований email збігається з введеним
        user = next((u for u in users if u.email == form.email.data), None)
        
        # Перевіряємо пароль
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Ви успішно увійшли в систему!', 'success')
            
            # Редирект залежно від ролі
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.index'))
        else:
            flash('Невірний email або пароль', 'danger')
            
    # 4. Передаємо об'єкт form у шаблон (це виправить UndefinedError)
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    # Очищення сесії для безпеки (як ти і хотів)
    from flask import session
    session.clear() 
    flash('Ви вийшли з системи', 'info')
    return redirect(url_for('main.index'))