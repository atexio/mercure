Git Quickstart
==============

Requirements
------------

-  python >= 3.5
-  pip

Deployment
----------

At first remember that Mercure is only compatible with Python 3. When
using pip and manage.py ensure that ``pip -V`` and ``python -V`` are
Python3 versions. You can use *virtualenv* to define python 3 as the
default version for a project without changing system wide version

::

    git clone git@github.com:synhack/mercure.git && cd mercure
    pip install -r requirements.txt
    ./manage.py makemigrations
    ./manage.py migrate
    ./manage.py collectstatic
    ./manage.py createsuperuser

    # In three different tabs
    ./manage.py runserver
    ./manage.py rqworker default
    ./manage.py rqscheduler
