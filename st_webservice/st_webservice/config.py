import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.urandom(16)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'db')

    OAUTH_CREDENTIALS = {
    'facebook': {
        'id': '324757018187796',
        'secret': 'ab3a308041765a67d3ea7244c66c245a'
    },
    'google': {
        'id': '1079434338675-eo84kf8cta3gcs688fp0tnk3f28j47eo.apps.googleusercontent.com',
        'secret': 'pUnbhL12msJv9FqKGcL9YJKv'
    },
    'github': {
        'id': 'b00648d6adf8b0b7c955',
        'secret': '3f74e1583d2dff3272856fb95529fb1e96f9e29a'
    }
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['dragonflareful@gmail.com']

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'