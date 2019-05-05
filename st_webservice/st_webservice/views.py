"""
Routes and views for the flask application.
"""
import os
from datetime import datetime
from flask import render_template
from st_webservice import app
from st_webservice.model.run_st import run_style_transfer
from st_webservice.utils import generate_image_filename, allowed_file
from tensorflow.keras.applications import VGG16, VGG19, InceptionV3

from flask import (Flask, flash, redirect, render_template, request,
send_from_directory, url_for)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from st_webservice.forms import LoginForm, RegistrationForm
from st_webservice.models import User, Image, db
from st_webservice.auth import OAuthSignIn

UPLOAD_CONTENT_FOLDER = 'st_webservice/static/images/upload/content/'
UPLOAD_STYLE_FOLDER = 'st_webservice/static/images/upload/style/'
TEMPLATE_CONTENT_FOLDER = 'st_webservice/static/images/content/'
TEMPLATE_STYLE_FOLDER = 'st_webservice/static/images/content/'
OUTPUT_IMAGE_FOLDER = 'st_webservice/static/images/output/images/'
OUTPUT_IMAGE_FORMAT = '.png'


MODEL_PARAMS = {
        'model_name' : VGG16,
        'num_iterations' : 100,
        'content_weight':1e3, 
        'style_weight':1e-2,
        'lr':5,
        'beta1':0.99,
        'epsilon':1e-1,
        'cfg_path':'static/images/output/graphs/'
}

OUTPUT_PARAMS = {}



@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        year=datetime.now().year,
    )

@app.route('/gallery')
def gallery():
    """Renders the gallery page."""
    return render_template(
        'gallery.html',
        year=datetime.now().year,
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        year=datetime.now().year,
    )

@app.route('/reset_pwd')
def reset_pwd():
    """Renders the reset password page."""
    return render_template(
        'reset_pwd.html',
        year=datetime.now().year,
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('style'))
        log_username = request.form.get('log_username')
        log_password = request.form.get('log_password')
        log_remember_me = request.form.get('log_remember')
        user = User.query.filter_by(username=log_username).first()
        if user is None or not user.check_password(log_password):
            error = 'Invalid username or password.'
            return render_template('login.html', title='Sign In', error=error)
        login_user(user, remember=log_remember_me)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('style')
        return redirect(next_page)
    return render_template('login.html', title='Sign In')


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('style'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('style'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, social_username, social_email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('login'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, social_username=social_username, social_email=social_email, username=None, email=None)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('style'))
        


@app.route('/logout')
def logout():
    logout_user()
    message = 'You have been successfully logged out.'
    return render_template('index.html', message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('style'))
        reg_username = request.form.get('reg_username')
        reg_password = request.form.get('reg_password')
        reg_rpassword = request.form.get('reg_rpassword')
        reg_email = request.form.get('reg_email')
        if reg_password != reg_rpassword:
            error = 'Passwords must match.'
            return render_template('register.html', title='Register', error=error)

        user = User.query.filter_by(username=reg_username).first()
        email = User.query.filter_by(email=reg_email).first()
        if user is not None:
            error = 'User already exists.'
            return render_template('register.html', title='Register', error=error)

        if email is not None:
            error = 'Account with this email already exists.'
            return render_template('register.html', title='Register', error=error)

        user = User(social_id=None, social_username=None, social_email=None, username=reg_username, email=reg_email)
        user.set_password(reg_password)
        db.session.add(user)
        db.session.commit()
        flash('You have been successfully registered to Style AI!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/style', methods=['GET', 'POST'])
@login_required
def style():
    """Renders the style page."""
    if request.method == 'POST':
        app.logger.info('Saving images..')
        # check if the post request has the file part
        if 'content-file' and 'style-file' not in request.files:
            message = 'Incorrect number of files specified in request.'
            app.logger.error(message)
            flash(message)
            return redirect(request.url)
        content_file = request.files['content-file']
        style_file = request.files['style-file']
        files = [content_file, style_file]
        content_name = generate_image_filename()
        style_name = generate_image_filename()
        result_name = generate_image_filename()
        result_file_name, file_extension = os.path.splitext(result_name)
        file_names = [content_name, style_name]

        for i, file in enumerate(files):
            if file.filename == '':
                message = 'No selected file'
                app.logger.error(message)
                flash(message)
                return redirect(request.url)
            if not allowed_file(file.filename):
                if i==0:
                    message = 'Incorrect extension passed for content file'
                    flash(message)
                    app.logger.error(message)
                else:
                    message = 'Incorrect extension passed for style file'
                    flash(message)
                    app.logger.error(message)
                return redirect(request.url)
            if file:
                if i == 0:
                    file.save(os.path.join(UPLOAD_CONTENT_FOLDER, file_names[i]))
                else:
                    file.save(os.path.join(UPLOAD_STYLE_FOLDER, file_names[i]))


        OUTPUT_PARAMS = MODEL_PARAMS.copy();
        MODEL_PARAMS['content_path'] = "st_webservice/static/images/upload/content/" + file_names[0];
        MODEL_PARAMS['style_path'] = "st_webservice/static/images/upload/style/" + file_names[1];
        MODEL_PARAMS['result_path'] = "st_webservice/static/images/output/images/" + result_name;
        MODEL_PARAMS['loss_path'] = "st_webservice/static/images/output/graphs/" + result_file_name + "_loss" + file_extension;
        MODEL_PARAMS['exec_path'] = "st_webservice/static/images/output/graphs/" + result_file_name + "_time" + file_extension;
        
        app.logger.info('Initiating style transfer model..')

        #try:
        result_dict = run_style_transfer(**MODEL_PARAMS)
        #except:
           # message = "Invalid image resolution. Dimensions must be even and divisible numbers(ex. 512x256)."
            #app.logger.error(message)
           # return render_template('style.html', message=message)

        OUTPUT_PARAMS.update({
            'total_time': result_dict['total_time'],
            'total_loss': result_dict['total_losses'][-1].numpy(),
            'style_loss': result_dict['style_losses'][-1].numpy(),
            'content_loss': result_dict['content_losses'][-1].numpy(),
            'gen_image_width': result_dict['gen_image_width'],
            'gen_image_height': result_dict['gen_image_height'],
            'model_name': result_dict['model_name'],
            'content_path': "../static/images/upload/content/" + file_names[0],
            'style_path': "../static/images/upload/style/" + file_names[1],
            'result_path': "../static/images/output/images/" + result_name,
            'loss_path': "../static/images/output/graphs/" + result_file_name + "_loss" + file_extension,
            'exec_path': "../static/images/output/graphs/" + result_file_name + "_time" + file_extension,
        });

        if current_user.is_authenticated:
            image = Image(
                gen_image_path=OUTPUT_PARAMS['result_path'],
                gen_image_width=OUTPUT_PARAMS['gen_image_width'],
                gen_image_height=OUTPUT_PARAMS['gen_image_height'],
                num_iters=OUTPUT_PARAMS['num_iterations'],
                model_name=OUTPUT_PARAMS['model_name'],
                total_loss=str(OUTPUT_PARAMS['total_loss']),
                style_loss=str(OUTPUT_PARAMS['style_loss']),
                content_loss=str(OUTPUT_PARAMS['content_loss']),
                timestamp=datetime.utcnow(),
                user_id=current_user.id
                )
            image.set_user(current_user)
            db.session.add(image)
            db.session.commit()

            app.logger.info('Saved image to database.')


        #params_render = {
        #    'content': "../static/images/upload/content/" + file_names[0],
        #    'style': "../static/images/upload/style/" + file_names[1],
        #    'result': "../static/images/output/images/" + result_name
        #}
        
        return render_template('results.html', **OUTPUT_PARAMS)
    return render_template('style.html')

@app.route('/user_images/<id>')
@login_required
def user_images(id):

    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('login'))

    if user.user_images is None:
        return render_template('user_images.html', message="No images to show.")

    return render_template('user_images.html', images=user.user_images)

@app.route('/user_images/<id>/<user_image_id>/popup')
@login_required
def user_stats(id, user_image_id):

    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('login'))

    

    image = Image.query.filter_by(id=user_image_id).first()
    if image is None:
        return render_template('user_images.html', message="Undefined image.")

    return render_template('user_stats.html', user_image=image)
