web: waitress-serve --port=$PORT runserver:app
worker: celery -A st_webservice worker --pool=eventlet -l info