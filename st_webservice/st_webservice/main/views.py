"""
Routes and views for the flask application.
"""
import os
import simplejson as json
from datetime import datetime
from flask import render_template
from st_webservice import app
from st_webservice.auth.email import send_password_reset_email
from st_webservice.model.run_st import run_style_transfer
from st_webservice.main.utils import generate_image_filename, allowed_file

import tensorflow as tf
from tensorflow.keras.applications import VGG16, VGG19, InceptionV3

from flask import (Flask, flash, session, redirect, render_template, request,
send_from_directory, url_for)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from st_webservice.models import User, Image, db
from st_webservice.auth.oauth import OAuthSignIn

from st_webservice.main import bp

UPLOAD_CONTENT_FOLDER = 'st_webservice/static/images/upload/content/'
UPLOAD_STYLE_FOLDER = 'st_webservice/static/images/upload/style/'
TEMPLATE_CONTENT_FOLDER = 'st_webservice/static/images/content/'
TEMPLATE_STYLE_FOLDER = 'st_webservice/static/images/content/'
OUTPUT_IMAGE_FOLDER = 'st_webservice/static/images/output/images/'
OUTPUT_IMAGE_FORMAT = '.png'



MODEL_PARAMS = {
        'model_name' : VGG16,
        'num_iterations' : 100,
        'img_w': 256,
        'img_h': 256,
        'content_weight':1e3, 
        'style_weight':1e-2,
        'lr':5,
        'beta1':0.99,
        'epsilon':1e-1,
        'cfg_path':'static/images/output/graphs/'
}

OUTPUT_PARAMS = {}



@bp.route('/')
@bp.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        year=datetime.now().year,
    )

@bp.route('/gallery')
def gallery():
    """Renders the gallery page."""
    return render_template(
        'gallery.html',
        year=datetime.now().year,
    )

@bp.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        year=datetime.now().year,
    )


@bp.route('/style/<id>', methods=['GET', 'POST'])
@login_required
def style(id):
    
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
        MODEL_PARAMS['num_iterations'] = int(request.form.get('iter-select'))
        input_resolution = str(request.form.get('res-select')).split('x')
        MODEL_PARAMS['img_w'] = int(input_resolution[0])
        MODEL_PARAMS['img_h'] = int(input_resolution[1])
        
        app.logger.info('Initiating style transfer model..')
        app.logger.info('Selected image resolution: {}x{}'.format(MODEL_PARAMS['img_w'], MODEL_PARAMS['img_h']))
        app.logger.info('Selected number of iterations: {}'.format(MODEL_PARAMS['num_iterations']))

        try:
            result_dict = run_style_transfer(**MODEL_PARAMS)
        except TypeError:
           message = "TypeError: Invalid model type or input image types."
           app.logger.error(message)
           return render_template('style.html', message=message)
        except tf.errors.InvalidArgumentError:
           message = "Invalid image resolution. Dimensions must be even and divisible numbers(ex. 512x256)."
           app.logger.error(message)
           return render_template('style.html', message=message)

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
        session['total_loss'] = json.dumps(str(OUTPUT_PARAMS['total_loss']))
        session['style_loss'] = json.dumps(str(OUTPUT_PARAMS['style_loss']))
        session['content_loss'] = json.dumps(str(OUTPUT_PARAMS['content_loss']))
        for param in OUTPUT_PARAMS:
            if param not in ['total_loss','style_loss','content_loss']:
                session[param] = OUTPUT_PARAMS[param]


        return redirect(url_for('main.results', id=current_user.id))

    user = User.query.filter_by(id=id).first()
    if user.id != current_user.id:
        flash('Access denied: Incorrect user.')
        return redirect(url_for('auth.login'))

    return render_template('style.html', id=current_user.id)

@bp.route('/results/<id>')
@login_required
def results(id):

    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('auth.login'))

    if user.id != current_user.id:
        flash('Access denied: Incorrect user.')
        return redirect(url_for('auth.login'))

    return render_template('results.html', id=current_user.id)

@bp.route('/user_images/<id>')
@login_required
def user_images(id):

    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('auth.login'))

    if user.id != current_user.id:
        flash('Access denied: Incorrect user.')
        return redirect(url_for('auth.login'))

    if user.user_images.count() == 0:
        return render_template('user_images.html', images=user.user_images, message='No images to show.')

    return render_template('user_images.html', images=user.user_images)

@bp.route('/user_images/<id>/<user_image_id>/popup')
@login_required
def user_stats(id, user_image_id):

    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('auth.login'))

    if user.id != current_user.id:
        flash('Access denied: Incorrect user.')
        return redirect(url_for('auth.login'))

    image = Image.query.filter_by(id=user_image_id).first()
    if image is None:
        flash('Image deleted from local storage.')
        return redirect(url_for('main.user_images', id=user.id))

    return render_template('user_stats.html', user_image=image)

@bp.route('/user_images/<id>/<user_image_id>/delete')
@login_required
def delete_image(id, user_image_id):
    user = User.query.filter_by(id=id).first()
    if user is None:
        flash('Authentication failed: User does not exist.')
        return redirect(url_for('auth.login'))

    if user.id != current_user.id:
        flash('Access denied: Incorrect user.')
        return redirect(url_for('auth.login'))

    image = Image.query.filter_by(id=user_image_id).first()
    if image is None:
        flash('Image deleted from local storage.')
        return redirect(url_for('main.user_images', id=user.id))


    img_location = image.gen_image_path
    db.session.delete(image)
    db.session.commit()
    app.logger.info('Image successfully removed from database.')
    try:
        os.remove(os.path.join('st_webservice/', img_location[3:]))
    except FileNotFoundError:
        app.logger.error('File not found in path.')

    flash('Image deleted from local storage.')
    app.logger.info('Image deleted from local storage.')

    return redirect(url_for('main.user_images', id=user.id))

    

