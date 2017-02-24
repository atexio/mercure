Git Quickstart
==============

Requirements
------------

-  python3
-  pip

Deployment
----------

::

    git clone git@bitbucket.org:synhack/mercure.git && cd mercure
    pip install -r requirements.txt
    ./manage.py makemigrations
    ./manage.py migrate
    ./manage.py collectstatic
    ./manage.py createsuperuser
    ./manage.py runserver

