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

UPLOAD_CONTENT_FOLDER = 'st_webservice/static/images/upload/content/'
UPLOAD_STYLE_FOLDER = 'st_webservice/static/images/upload/style/'
TEMPLATE_CONTENT_FOLDER = 'st_webservice/static/images/content/'
TEMPLATE_STYLE_FOLDER = 'st_webservice/static/images/content/'
OUTPUT_IMAGE_FOLDER = 'st_webservice/static/images/output/images/'
OUTPUT_IMAGE_FORMAT = '.png'


MODEL_PARAMS = {
        'model_name' : VGG16,
        'num_iterations' : 300,
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

@app.route('/style', methods=['GET', 'POST'])
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

        try:
            result_dict = run_style_transfer(**MODEL_PARAMS)
        except:
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


        #params_render = {
        #    'content': "../static/images/upload/content/" + file_names[0],
        #    'style': "../static/images/upload/style/" + file_names[1],
        #    'result': "../static/images/output/images/" + result_name
        #}
        
        return render_template('results.html', **OUTPUT_PARAMS)
    return render_template('style.html')

@app.route('/results')
def results():
    """Renders the results page."""
    return render_template(
        'results.html',
        year=datetime.now().year,
    )