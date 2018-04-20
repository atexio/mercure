FROM python:3.6

ENV PYTHONUNBUFFERED 1

# add cron
RUN apt-get update
RUN apt-get install -y cron
COPY docker/crontab /etc/cron.d/mercure
# Fix secu update

# Activate continus security update

# Clean apt

# Install
COPY requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
RUN pip install gunicorn
COPY . /code/
RUN rm -r /code/docker
WORKDIR /code/

# Limit non root user user
RUN groupadd -r mercure --gid=999
RUN useradd -r -g mercure --uid=999 mercure
RUN chown -R mercure:mercure /code

# Prepare django
USER mercure
RUN python manage.py collectstatic --noinput

# Prepare scripts
USER root
COPY docker/init-volume.sh /code/init-volume.sh
COPY docker/run-server.sh /code/run-server.sh
RUN chmod +x /code/init-volume.sh
RUN chmod +x /code/run-server.sh
RUN chmod +x /code/scripts/cron.py


# test
RUN /usr/local/bin/python3 -V  # used in crontab

# Start django in limited right
EXPOSE 8000
USER root
CMD cron && /code/init-volume.sh && su mercure -c '/code/run-server.sh'
