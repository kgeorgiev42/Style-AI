import os

basedir = os.path.abspath(os.path.dirname(__file__))


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
