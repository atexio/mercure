Docker Quickstart
=================

Requirements
------------

-  docker
-  docker-compose

Available configuration
-----------------------

+-------------------+------+-----------------+-----------------------+
| Environment       | Stat | Description     | Value example         |
| variable name     | us   |                 |                       |
+===================+======+=================+=======================+
| SECRET_KEY        | Requ | Django secret   | Random string         |
|                   | ired | key             |                       |
+-------------------+------+-----------------+-----------------------+
| URL               | Requ | Mercure URL     | https://mercure.examp |
|                   | ired |                 | le.com                |
+-------------------+------+-----------------+-----------------------+
| EMAIL_HOST        | Requ | SMTP server     | mail.example.com      |
|                   | ired |                 |                       |
+-------------------+------+-----------------+-----------------------+
| EMAIL_PORT        | Opti | SMTP port       | 587                   |
|                   | onal |                 |                       |
+-------------------+------+-----------------+-----------------------+
| EMAIL_HOST_USER   | Opti | SMTP user       | phishing@example.com  |
|                   | onal |                 |                       |
+-------------------+------+-----------------+-----------------------+
| EMAIL_HOST_PASSWO | Opti | SMTP password   | P@SSWORD              |
| RD                | onal |                 |                       |
+-------------------+------+-----------------+-----------------------+
| REDIS_HOST        | Opti | Redis server    | 127.0.0.1             |
|                   | onal |                 |                       |
+-------------------+------+-----------------+-----------------------+
| REDIS_PORT        | Opti | Redis port      | 6379                  |
|                   | onal |                 |                       |
+-------------------+------+-----------------+-----------------------+
| DEBUG             | Opti | Run on debug    | True                  |
|                   | onal | mode            |                       |
+-------------------+------+-----------------+-----------------------+
| SENTRY_DSN        | Opti | Send debug info | https://23xxx:38xxx@s |
|                   | onal | to sentry.io    | entry.io/1234         |
+-------------------+------+-----------------+-----------------------+
| AXES_LOCK_OUT_AT_ | Opti | Ban on          | True                  |
| FAILURE           | onal | forcebrute      |                       |
|                   |      | login           |                       |
+-------------------+------+-----------------+-----------------------+
| AXES_COOLOFF_TIME | Opti | Ban duration on | 0.8333                |
|                   | onal | forcebrute      |                       |
|                   |      | login (in       |                       |
|                   |      | hours)          |                       |
+-------------------+------+-----------------+-----------------------+
| DONT_SERVES_STATI | Opti | Don’t serve     | True                  |
| C_FILE            | onal | static files    |                       |
|                   |      | with django     |                       |
+-------------------+------+-----------------+-----------------------+

Sample deployment
-----------------

.. code:: yaml

    version: '2'

    services:
      redis:
        image: redis
        restart: always
        volumes:
          - /etc/localtime:/etc/localtime:ro
      front:
        image: synhackfr/mercure
        restart: always
        links:
          - redis:redis
        ports:
          - 8000:8000
        volumes:
          - ./data/db:/usr/src/app/data
          - ./data/media:/usr/src/app/media
          - /etc/localtime:/etc/localtime:ro
        environment:
          - SECRET_KEY=<random value>
          - EMAIL_HOST=mail.example.com
          - EMAIL_PORT=587
          - EMAIL_HOST_USER=phishing@example.com
          - EMAIL_HOST_PASSWORD=P@SSWORD

To generate the SECRET_KEY variable, you can use this command:

.. code:: shell

    # generate random SECRET_KEY
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 200 | head -n 1

The SECRET_KEY is used as a salt for django password hashing, don’t
change it after using it with mercure. After changing the secret key,
you can run the container with this command:

.. code:: shell

    docker-compose up -d

Next, you can create a super user to log into web interface:

.. code:: bash

    # create super user
    docker-compose exec front python manage.py createsuperuser
