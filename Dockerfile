FROM python:3-onbuild

# To handle buildable attachments
RUN apt-get update && apt-get install -y zip unzip supervisor

# prepare django
RUN python manage.py makemigrations
RUN python manage.py collectstatic --noinput
RUN cp docker/django.conf /etc/supervisor/conf.d/

# start django
EXPOSE 8000
CMD python manage.py migrate && supervisord -n
