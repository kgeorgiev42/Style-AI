web: waitress-serve --port=5000 runserver:app
worker: celery -A st_webservice worker --pool=eventlet -l info