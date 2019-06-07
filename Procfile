web: waitress-serve --port=$PORT --channel-timeout=20000 runserver:app
worker: celery -A st_webservice worker --pool=eventlet -l info