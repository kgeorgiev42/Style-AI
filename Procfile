web: waitress-serve --port=$PORT --url-scheme=https runserver:app
worker: celery -A st_webservice worker --pool=eventlet -l info