from flask import Blueprint

bp = Blueprint('errors', __name__)

from st_webservice.errors import handlers
