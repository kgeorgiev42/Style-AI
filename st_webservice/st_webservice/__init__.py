"""
The flask application package.
"""

import os
from flask import Flask
from st_webservice.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail



app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
lm = LoginManager(app)
lm.login_view = 'login'
db.create_all()

from st_webservice.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from st_webservice.auth import bp as auth_bp
app.register_blueprint(auth_bp)

from st_webservice.main import bp as main_bp
app.register_blueprint(main_bp)



import st_webservice.main.views
