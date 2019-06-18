from flask import Blueprint

bp = Blueprint('model', __name__)

from st_webservice.main import views, utils
from st_webservice.model import run_st

