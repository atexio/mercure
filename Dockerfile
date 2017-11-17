FROM python:3-alpine

# To handle buildable attachments and compile cchardet
RUN apk update && apk add --no-cache zip unzip g++ libc-dev supervisor

# Do like debian "onbuild" versions
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app

# prepare django
RUN python manage.py makemigrations
RUN python manage.py collectstatic --noinput
RUN cp docker/django.conf /etc/supervisor/conf.d/

# start django
EXPOSE 8000
CMD python manage.py migrate && supervisord -n
