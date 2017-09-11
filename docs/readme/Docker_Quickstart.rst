Docker Quickstart
=================

Requirements
------------

-  docker

Available configuration
-----------------------

+------------------+--------+----------------------------+----------------------+
| Environment      | Status | Description                | Value example        |
| variable name    |        |                            |                      |
+==================+========+============================+======================+
| SECRET\_KEY      | Requir | Django secret key          | Random string        |
|                  | ed     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| URL              | Requir | Mercure URL                | https://mercure.exam |
|                  | ed     |                            | p                    |
|                  |        |                            | le.com               |
+------------------+--------+----------------------------+----------------------+
| EMAIL\_HOST      | Requir | SMTP server                | mail.example.com     |
|                  | ed     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| EMAIL\_PORT      | Option | SMTP port                  | 587                  |
|                  | al     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| EMAIL\_HOST\_USE | Option | SMTP user                  | phishing@example.com |
| R                | al     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| EMAIL\_HOST\_PAS | Option | SMTP password              | P@SSWORD             |
| SWORD            | al     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| DEBUG            | Option | Run on debug mode          | True                 |
|                  | al     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| SENTRY\_DSN      | Option | Send debug info to         | https://23xxx:38xxx@ |
|                  | al     | sentry.io                  | s                    |
|                  |        |                            | entry.io/1234        |
+------------------+--------+----------------------------+----------------------+
| AXES\_LOCK\_OUT  | Option | Ban on forcebrute login    | True                 |
| \_AT\_FAILURE    | al     |                            |                      |
+------------------+--------+----------------------------+----------------------+
| AXES\_COOLOFF\_T | Option | Ban duration on forcebrute | 0.8333               |
| IME              | al     | login (in hours)           |                      |
+------------------+--------+----------------------------+----------------------+
| DONT\_SERVES\_ST | Option | Don't serve static files   | True                 |
| ATIC\_FILE       | al     | with django                |                      |
+------------------+--------+----------------------------+----------------------+

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
