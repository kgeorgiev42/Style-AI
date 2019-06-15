"""
Routes and views for the flask application.
"""
import os
import simplejson as json
import flask
import logging

from logging.handlers import RotatingFileHandler

from datetime import datetime
from st_webservice.auth.email import send_password_reset_email
from st_webservice.model.run_st import run_style_transfer
from st_webservice.main.utils import generate_image_filename, allowed_file

from flask_sqlalchemy import get_debug_queries
import tensorflow as tf

from flask import (Flask, flash, session, redirect, render_template, request,
send_from_directory, url_for, current_app, jsonify)
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from st_webservice.models import User, Image, db
from st_webservice.auth.oauth import OAuthSignIn

from st_webservice.main import bp

from st_webservice import celery




handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
logger.addHandler(handler)

@bp.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASK_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                    (query.statement, query.parameters, query.duration,
                     query.context))
    return response

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

@bp.route('/status/<task_id>/<user_id>')
def status(task_id, user_id):

    task = run_style_transfer.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'total_loss': '',
            'content_loss': '',
            'style_loss': '',
            'cur_time': '',
            'status': 'Pending'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'total_loss': task.info.get('total_loss', ''),
            'content_loss': task.info.get('content_loss', ''),
            'style_loss': task.info.get('style_loss', ''),
            'cur_time': task.info.get('cur_time', ''),
            'status': task.info.get('status', '')
        }
    elif task.state == 'COMPLETE' or task.state == 'SUCCESS':
        user = User.query.filter_by(id=user_id).first()
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'total_loss': task.info.get('total_loss', ''),
            'content_loss': task.info.get('content_loss', ''),
            'style_loss': task.info.get('style_loss', ''),
            'cur_time': task.info.get('cur_time', ''),
            'user_id': user_id, 
            'status': 'Finished'
        }
        output_filename_ct = current_app.config['MODEL_PARAMS']['content_path'].split('/')[-1]
        output_filename_st = current_app.config['MODEL_PARAMS']['style_path'].split('/')[-1]
        output_filename_res = current_app.config['MODEL_PARAMS']['result_path'].split('/')[-1]
        result_file_name, file_extension = os.path.splitext(output_filename_res)
        current_app.config['OUTPUT_PARAMS'].update({
            'total_time': task.info['total_time'],
            'total_loss': json.loads(task.info['total_losses'])[-1],
            'style_loss': json.loads(task.info['style_losses'])[-1],
            'content_loss': json.loads(task.info['content_losses'])[-1],
            'gen_image_width': task.info['gen_image_width'],
            'gen_image_height': task.info['gen_image_height'],
            'model_name': task.info['model_name'],
            'num_iterations': int(task.info['total']),
            'content_path': "../static/images/upload/content/" + output_filename_ct,
            'style_path': "../static/images/upload/style/" + output_filename_st,
            'result_path': "../static/images/output/images/" + output_filename_res,
            'loss_path': "../static/images/output/graphs/" + result_file_name + "_loss" + file_extension,
            'exec_path': "../static/images/output/graphs/" + result_file_name + "_time" + file_extension,
        });

        
        if user.is_authenticated:
            image = Image(
                gen_image_path=current_app.config['OUTPUT_PARAMS']['result_path'],
                gen_image_width=current_app.config['OUTPUT_PARAMS']['gen_image_width'],
                gen_image_height=current_app.config['OUTPUT_PARAMS']['gen_image_height'],
                num_iters=current_app.config['OUTPUT_PARAMS']['num_iterations'],
                model_name=current_app.config['OUTPUT_PARAMS']['model_name'],
                total_loss=str(current_app.config['OUTPUT_PARAMS']['total_loss']),
                style_loss=str(current_app.config['OUTPUT_PARAMS']['style_loss']),
                content_loss=str(current_app.config['OUTPUT_PARAMS']['content_loss']),
                timestamp=datetime.utcnow(),
                user_id=user_id
                )
            
            image.set_user(user)
            db.session.add(image)
            db.session.commit()

            logger.info('Saved image to database.')


        #params_render = {
        #    'content': "../static/images/upload/content/" + file_names[0],
        #    'style': "../static/images/upload/style/" + file_names[1],
        #    'result': "../static/images/output/images/" + result_name
        #}
        session['total_loss'] = json.dumps(current_app.config['OUTPUT_PARAMS']['total_loss'])
        session['style_loss'] = json.dumps(current_app.config['OUTPUT_PARAMS']['style_loss'])
        session['content_loss'] = json.dumps(current_app.config['OUTPUT_PARAMS']['content_loss'])
        for param in current_app.config['OUTPUT_PARAMS']:
            if param not in ['total_loss','style_loss','content_loss']:
                session[param] = current_app.config['OUTPUT_PARAMS'][param]
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@bp.route('/style', methods=['GET', 'POST'])
@login_required
def style():
    """Renders the style page.""" 
    if request.method == 'GET':
        return render_template('style.html')
    return redirect(url_for('main.style'))
    
      
@bp.route('/st_task', methods=['POST'])
def st_task():
    logger.info('Saving images..')
    # check if the post request has the file part
    if 'content-file' and 'style-file' not in request.files:
        message = 'Incorrect number of files specified in request.'
        logger.error(message)
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
            logger.error(message)
            flash(message)
            return redirect(request.url)
        if not allowed_file(file.filename):
            if i==0:
                message = 'Incorrect extension passed for content file'
                flash(message)
                logger.error(message)
            else:
                message = 'Incorrect extension passed for style file'
                flash(message)
                logger.error(message)
            return redirect(request.url)
        if file:
            if i == 0:
                print('Saving content file..')
                file.save(os.path.join(current_app.config['UPLOAD_CONTENT_FOLDER'], file_names[i]))
            else:
                print('Saving style file..')
                file.save(os.path.join(current_app.config['UPLOAD_STYLE_FOLDER'], file_names[i]))


    current_app.config['OUTPUT_PARAMS'] = current_app.config['MODEL_PARAMS'].copy();
    current_app.config['MODEL_PARAMS']['content_path'] = current_app.config['UPLOAD_CONTENT_FOLDER'] + file_names[0];
    current_app.config['MODEL_PARAMS']['style_path'] = current_app.config['UPLOAD_STYLE_FOLDER'] + file_names[1];
    current_app.config['MODEL_PARAMS']['result_path'] = current_app.config['OUTPUT_IMAGE_FOLDER'] + result_name;
    current_app.config['MODEL_PARAMS']['loss_path'] = current_app.config['OUTPUT_STAT_FOLDER'] + result_file_name + "_loss" + file_extension;
    current_app.config['MODEL_PARAMS']['exec_path'] = current_app.config['OUTPUT_STAT_FOLDER'] + result_file_name + "_time" + file_extension;
    current_app.config['MODEL_PARAMS']['num_iterations'] = int(request.form.get('iter-select'))
    input_resolution = str(request.form.get('res-select')).split('x')
    current_app.config['MODEL_PARAMS']['img_w'] = int(input_resolution[0])
    current_app.config['MODEL_PARAMS']['img_h'] = int(input_resolution[1])

    logger.info('Initiating style transfer model..')
    logger.info('Selected image resolution: {}x{}'.format(current_app.config['MODEL_PARAMS']['img_w'], current_app.config['MODEL_PARAMS']['img_h']))
    logger.info('Selected number of iterations: {}'.format(current_app.config['MODEL_PARAMS']['num_iterations']))

    try:
        task = run_style_transfer.apply_async([str(current_app.config['MODEL_PARAMS']['content_path']),
                                                str(current_app.config['MODEL_PARAMS']['style_path']),
                                                str(current_app.config['MODEL_PARAMS']['result_path']),
                                                str(current_app.config['MODEL_PARAMS']['loss_path']),
                                                str(current_app.config['MODEL_PARAMS']['exec_path']),
                                                int(current_app.config['MODEL_PARAMS']['num_iterations']),
                                                int(current_app.config['MODEL_PARAMS']['img_w']),
                                                int(current_app.config['MODEL_PARAMS']['img_h'])])

        return jsonify({}), 202, {'Location': url_for('main.status',
                                                task_id=task.id, user_id=current_user.id)}
        #return redirect(url_for('main.status', task_id=task.id))
        #async_result = celery.AsyncResult(id=task.task_id)
        #result_dict = async_result.get()
    #except TypeError:
        #message = "TypeError: Invalid model type or input image types."
        #logger.error(message)
        #return render_template('style.html', message=message)
    except tf.errors.InvalidArgumentError:
        message = "Invalid image resolution. Dimensions must be even and divisible numbers(ex. 512x256)."
        logger.error(message)
        return render_template('style.html', message=message)
    

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
        flash('No images to show.')
        return render_template('user_images.html', images=user.user_images)

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
        flash('Image not found.')
        return redirect(url_for('main.user_images', id=user.id))


    img_location = image.gen_image_path
    db.session.delete(image)
    db.session.commit()
    message = 'Image successfully removed from database.'
    logger.info(message)
    print(message)
    try:
        os.remove(os.path.join('st_webservice/', img_location[3:]))
    except FileNotFoundError:
        logger.error('File not found in path.')

    message = 'Image successfully removed from disk.'
    flash(message)
    logger.info(message)

    return redirect(url_for('main.user_images', id=user.id))

