from st_webservice.auth import bp

from flask import (Flask, flash, session, redirect, render_template, request,
send_from_directory, url_for)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from st_webservice.models import User, Image, db
from st_webservice.auth.oauth import OAuthSignIn

import os
import simplejson as json
from datetime import datetime
from flask import render_template
from st_webservice.auth.email import send_password_reset_email

@bp.route('/reset_pwd', methods=['GET', 'POST'])
def reset_pwd():
    """Renders the reset password page."""
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('main.style', id=current_user.id))
        email = request.form.get('resetEmail')
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for the instructions to reset your password')
        else:
            flash('No user exists with this email address.')
        return redirect(url_for('auth.login'))
    return render_template(
        'auth/reset_pwd.html',
        year=datetime.now().year,
    )

@bp.route('/reset_pwd_token/<token>', methods=['GET', 'POST'])
def reset_pwd_token(token):
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('main.style', id=current_user.id))
        user = User.verify_reset_password_token(token)
        if not user:
            flash('Access Denied: Incorrect Password Token.')
            return redirect(url_for('auth.login'))

        user_pass = request.form.get('resetPassword')
        user_pass2 = request.form.get('resetPassword2')

        if user_pass != user_pass2:
            error = 'Passwords must match.'
            return render_template('auth/reset_pwd_token.html', title='Reset Password', error=error)
        
        user.set_password(user_pass)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_pwd_token.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('main.style', id=current_user.id))
        log_username = request.form.get('log_username')
        log_password = request.form.get('log_password')
        log_remember_me = request.form.get('log_remember')
        user = User.query.filter_by(username=log_username).first()
        if user is None or not user.check_password(log_password):
            error = 'Invalid username or password.'
            return render_template('auth/login.html', title='Sign In', error=error)
        login_user(user, remember=log_remember_me)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.style', id=current_user.id)
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In')


@bp.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.style', id=current_user.id))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@bp.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.style', id=current_user.id))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, social_username, social_email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, social_username=social_username, social_email=social_email, username=None, email=None)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('main.style', id=current_user.id))
        


@bp.route('/logout')
def logout():
    logout_user()
    message = 'You have been successfully logged out.'
    return render_template('index.html', message=message)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('main.style', id=current_user.id))
        reg_username = request.form.get('reg_username')
        reg_password = request.form.get('reg_password')
        reg_rpassword = request.form.get('reg_rpassword')
        reg_email = request.form.get('reg_email')
        if reg_password != reg_rpassword:
            error = 'Passwords must match.'
            return render_template('auth/register.html', title='Register', error=error)

        user = User.query.filter_by(username=reg_username).first()
        email = User.query.filter_by(email=reg_email).first()
        if user is not None:
            error = 'User already exists.'
            return render_template('auth/register.html', title='Register', error=error)

        if email is not None:
            error = 'Account with this email already exists.'
            return render_template('auth/register.html', title='Register', error=error)

        user = User(social_id=None, social_username=None, social_email=None, username=reg_username, email=reg_email)
        user.set_password(reg_password)
        db.session.add(user)
        db.session.commit()
        flash('You have been successfully registered to Style AI!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register')
