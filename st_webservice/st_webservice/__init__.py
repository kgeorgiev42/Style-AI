"""
The flask application package.
"""

import os
from flask import Flask
from st_webservice.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)
lm = LoginManager(app)
lm.login_view = 'login'
db.create_all()

import st_webservice.views