"""
This script runs the st_webservice application using a development server.
"""
import os
from os import environ
from st_webservice import app
import logging
from logging.handlers import SMTPHandler


if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5000'))
    except ValueError:
        PORT = 5000

    app.debug = True
    app.run(HOST, PORT, threaded=True)
