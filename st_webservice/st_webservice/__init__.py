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


db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
lm = LoginManager()
lm.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    lm.init_app(app)

    from st_webservice.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from st_webservice.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from st_webservice.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


import st_webservice.main.views, st_webservice.models