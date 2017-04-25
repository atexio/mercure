FROM python:3-onbuild

# To handle buildable attachments
RUN apt-get update && apt-get install -y zip unzip

# prepare django
RUN python manage.py makemigrations
RUN python manage.py collectstatic --noinput


# start django
EXPOSE 8000
CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000
