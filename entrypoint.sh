#!bin/bash -x

gunicorn backend.wsgi:application -b 194.58.108.226:8000 --reload