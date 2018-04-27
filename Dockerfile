FROM python:3.6

ENV PYTHONUNBUFFERED 1

# add cron
RUN apt-get update
RUN apt-get install -y cron
COPY docker/crontab /etc/cron.d/mercure

# Clean apt
RUN apt-get autoremove -y
RUN apt-get clean && apt-get autoclean
RUN rm -rf /tmp/* /var/tmp/*
RUN rm -rf /var/lib/apt/lists/*
RUN rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin

# test
RUN /usr/local/bin/python3 -V  # used in crontab

# Prepare scripts
COPY docker/init-with-root.sh /root/init-with-root.sh
COPY docker/start-without-root.sh /code/start-without-root.sh
RUN chmod +x /root/init-with-root.sh
RUN chmod +x /code/start-without-root.sh

# Install Django
COPY requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
RUN pip install gunicorn
COPY . /code/
RUN rm -r /code/docker
RUN chmod +x /code/scripts/cron.py
WORKDIR /code/

# Limit non root user user
RUN groupadd -r mercure --gid=999
RUN useradd -r -g mercure --uid=999 mercure
RUN chown -R mercure:mercure /code

# Prepare django
USER mercure
RUN python manage.py collectstatic --noinput

# Start django in limited right
EXPOSE 8000
USER root
CMD cron && /root/init-with-root.sh && su mercure -c '/code/start-without-root.sh'
