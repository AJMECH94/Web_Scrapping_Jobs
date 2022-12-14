#celery worker for Linux
celery -A tasks.celery worker --loglevel=info

#celery worker for windows
celery -A tasks.celery worker -l info --pool=solo
celery -A crawl.celery worker -l info --pool=solo
celery -A tasks.celery worker -l info --pool=prefork
celery -A crawl.celery worker -l info --pool=prefork
celery -A tasks.celery worker -l info --pool=gevent
celery -A crawl.celery worker -l info --pool=gevent----> working

#celery beat
celery -A tasks beat --loglevel=info

#celery flower
celery -A tasks flower --address=127.0.0.1 --port=5555