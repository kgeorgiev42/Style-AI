from flask import Blueprint

bp = Blueprint('auth', __name__)

from st_webservice.auth import email, oauth, forms, routes


