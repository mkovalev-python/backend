#!bin/bash -x

sleep 60


python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic

echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@example.ru','admin')" | python manage.py shell
gunicorn backend.wsgi:application -b 0.0.0.0:8000 --reload