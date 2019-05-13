import warnings
warnings.filterwarnings("ignore")
import os
from flask import (Flask, flash, redirect, render_template, request,
send_from_directory, url_for)


from st_webservice import app


@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)
