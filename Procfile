web: gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 main:app
worker: python notification_worker.py