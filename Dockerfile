FROM python:3-onbuild


# prepare django
RUN python manage.py makemigrations
RUN python manage.py collectstatic --noinput


# start django
EXPOSE 8000
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000