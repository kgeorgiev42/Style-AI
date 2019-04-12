"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template
from st_webservice import app

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

@app.route('/style')
def style():
    """Renders the style page."""
    return render_template(
        'style.html',
        year=datetime.now().year,
    )