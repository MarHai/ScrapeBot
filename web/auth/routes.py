from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from web.auth import bp
from web.auth.forms import LoginForm
from scrapebot.database import User
from web import db


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_to_next_or_dashboard()
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data) or not user.active:
            flash('Incorrect username and/or password.')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect_to_next_or_dashboard()
    return render_template('auth/login.html', form=form)


def redirect_to_next_or_dashboard():
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('main.dashboard')
    return redirect(next_page)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
