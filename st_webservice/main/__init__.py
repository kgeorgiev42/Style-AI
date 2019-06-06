from flask import Blueprint

bp = Blueprint('main', __name__)

from st_webservice.main import views, utils
