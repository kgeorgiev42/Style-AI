import os
from dotenv import load_dotenv
from tensorflow.keras.applications import VGG16, VGG19, InceptionV3

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.urandom(16)

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
    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_SLOW_DB_QUERY_TIME = 0.5
    
    LOCAL_CONTENT_FOLDER = 'static/images/upload/content/'
    LOCAL_STYLE_FOLDER = 'static/images/upload/style/'
    UPLOAD_CONTENT_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/upload/content/'
    UPLOAD_STYLE_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/upload/style/'
    TEMPLATE_CONTENT_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/content/'
    TEMPLATE_STYLE_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/style/'
    OUTPUT_IMAGE_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/output/images/'
    OUTPUT_STAT_FOLDER = 'https://styleai.s3.amazonaws.com/static/images/output/graphs/'

    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    FLASKS3_BUCKET_NAME = 'styleai'
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(FLASKS3_BUCKET_NAME)
    S3_OBJECT_URL = 'https://styleai.s3.us-east-2.amazonaws.com/'
    
    MODEL_PARAMS = {
            'model_name' : VGG16,
            'num_iterations' : 100,
            'img_w': 256,
            'img_h': 256,
            'content_weight':1e3, 
            'style_weight':1e-2,
            'lr':5,
            'beta1':0.99,
            'epsilon':1e-1,
            'cfg_path':OUTPUT_STAT_FOLDER
    }

    OUTPUT_PARAMS = {}

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASK_MAIL_SUBJECT_PREFIX = '[StyleAI]'
    FLASK_MAIL_SENDER = 'StyleAI Admin <ivantestov4242@gmail.com>'
    FLASK_ADMIN = os.environ.get('FLASK_ADMIN')
    SSL_REDIRECT = False
    ADMINS = ['ivantestov4242@gmail.com']

    CELERY_BROKER_URL = os.environ['REDIS_URL'] #'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ['REDIS_URL'] #'redis://localhost:6379/0'

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False
    UPLOAD_CONTENT_FOLDER = 'st_webservice/static/test/images/upload/content/'
    UPLOAD_STYLE_FOLDER = 'st_webservice/static/test/images/upload/style/'
    OUTPUT_IMAGE_FOLDER = 'st_webservice/static/test/images/output/images/'
    OUTPUT_STAT_FOLDER = 'st_webservice/static/test/images/output/graphs/'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASK_MAIL_SENDER,
            toaddrs=[cls.FLASK_ADMIN],
            subject=cls.FLASK_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
    }