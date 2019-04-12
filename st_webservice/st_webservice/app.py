import warnings
warnings.filterwarnings("ignore")
import os
from flask import (Flask, flash, redirect, render_template, request,
send_from_directory, url_for)
import jinja2

from werkzeug.utils import secure_filename
from model import run_st

import cv2
import random
import string

import st_webservice.views


app = Flask(__name__)

UPLOAD_CONTENT_FOLDER = './static/images/upload/content/'
UPLOAD_STYLE_FOLDER = './static/images/upload/style/'
TEMPLATE_CONTENT_FOLDER = './static/images/content/'
TEMPLATE_STYLE_FOLDER = './static/images/content/'
OUTPUT_IMAGE_FOLDER = './static/images/output/images/'
OUTPUT_IMAGE_FORMAT = '.png'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app.config['UPLOAD_STYLE_FOLDER'] = UPLOAD_STYLE_FOLDER
app.config['UPLOAD_CONTENT_FOLDER'] = UPLOAD_CONTENT_FOLDER

def generate_image_filename():
    return str(uuid.uuid4()) + '.png'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)


@app.route('/styles/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'content-file' and 'style-file' not in request.files:
            flash('Incorrect number of files specified in request.')
            return redirect(request.url)
        content_file = request.files['content-file']
        style_file = request.files['style-file']
        files = [content_file, style_file]
        content_name = generate_image_filename()
        style_name = generate_image_filename()
        file_names = [content_name, style_name]

        for i, file in enumerate(files):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                if i == 0:
                    file.save(os.path.join(app.config['UPLOAD_CONTENT_FOLDER'], file_names[i]))
                else:
                    file.save(os.path.join(app.config['UPLOAD_STYLE_FOLDER'], file_names[i]))
                # return redirect(url_for('uploaded_file',
                #                        filename=filename))

        result_dict = run_model(file_names[0], file_names[1])
        params = {
            'content': "static/images/content/" + file_names[0],
            'style': "static/images/style/" + file_names[1],
            'result': "static/images/output/images/" + result_filename
        }
        return render_template('success.html', **params)
    return render_template('style.html')