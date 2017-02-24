Docker Quickstart
=================

Requirements
------------

-  docker

Available configuration
-----------------------

+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| Environment variable name      | Status     | Description                                   | Value example                        |
+================================+============+===============================================+======================================+
| SECRET\_KEY                    | Required   | Django secret key                             | Random string                        |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| URL                            | Required   | Mercure URL                                   | https://mercure.example.com          |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| EMAIL\_HOST                    | Required   | SMTP server                                   | mail.example.com                     |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| EMAIL\_PORT                    | Optional   | SMTP port                                     | 587                                  |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| EMAIL\_HOST\_USER              | Optional   | SMTP user                                     | phishing@example.com                 |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| EMAIL\_HOST\_PASSWORD          | Optional   | SMTP password                                 | P@SSWORD                             |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| DEBUG                          | Optional   | Run on debug mode                             | True                                 |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| SENTRY\_DSN                    | Optional   | Send debug info to sentry.io                  | https://23xxx:38xxx@sentry.io/1234   |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| AXES\_LOCK\_OUT\_AT\_FAILURE   | Optional   | Ban on forcebrute login                       | True                                 |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| AXES\_COOLOFF\_TIME            | Optional   | Ban duration on forcebrute login (in hours)   | 0.8333                               |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+
| DONT\_SERVES\_STATIC\_FILE     | Optional   | Don't serve static files with django          | True                                 |
+--------------------------------+------------+-----------------------------------------------+--------------------------------------+

Sample deployment
-----------------

.. code:: shell

    # create container
    docker run \
        -d \
        --name=mercure \
        -e SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 200 | head -n 1) \
        -e URL=https://mercure.example.com \
        -e EMAIL_HOST=mail.example.com \
        -e EMAIL_PORT=587 \
        -e EMAIL_HOST_USER=phishing@example.com \
        -e EMAIL_HOST_PASSWORD=P@SSWORD \
        synhackfr/mercure

    # create super user
    docker exec -it mercure python manage.py createsuperuser

