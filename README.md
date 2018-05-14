# Mercure

[![Build Status](https://travis-ci.org/atexio/mercure.svg?branch=master)](https://travis-ci.org/atexio/mercure)
[![Coverage Status](https://coveralls.io/repos/github/atexio/mercure/badge.svg?branch=master)](https://coveralls.io/github/atexio/mercure?branch=master)
[![Documentation Status](https://readthedocs.org/projects/mercure/badge/?version=latest)](http://doc.mercure.io/en/latest/?badge=latest)
[![Code Health](https://landscape.io/github/atexio/mercure/master/landscape.svg?style=flat)](https://landscape.io/github/atexio/mercure/master)
[![Requirements Status](https://requires.io/github/atexio/mercure/requirements.svg?branch=master)](https://requires.io/github/atexio/mercure/requirements/?branch=master)

Mercure is a tool for security managers who want to teach their colleagues about phishing.


## What Mercure can do:

* Create email templates
* Create target lists
* Create landing pages
* Handle attachments
* Let you keep track in the Campaign dashboard
* Track email reads, landing page visits and attachment execution.
* Harvest credentials
* Schedule campaigns
* Minimize link in email templates


## What Mercure will do:

* Display more graphs (we like graphs!)
* Provide a REST API
* Allow for multi-message campaigns (aka scenarios)
* Check browser plugins
* User training

# Docker Quickstart

## Requirements

* docker
* docker-compose

## Available configuration

| Environment variable name | Status   | Description                                 | Value example                      |
|---------------------------|----------|---------------------------------------------|------------------------------------|
| SECRET_KEY                | Required | Django secret key                           | Random string                      |
| URL                       | Required | Mercure URL                                 | https://mercure.example.com        |
| EMAIL_HOST                | Required | SMTP server                                 | mail.example.com                   |
| EMAIL_PORT                | Optional | SMTP port                                   | 587                                |
| EMAIL_HOST_USER           | Optional | SMTP user                                   | phishing@example.com               |
| EMAIL_HOST_PASSWORD       | Optional | SMTP password                               | P@SSWORD                           |
| DEBUG                     | Optional | Run on debug mode                           | True                               |
| SENTRY_DSN                | Optional | Send debug info to sentry.io                | https://23xxx:38xxx@sentry.io/1234 |
| AXE_DISABLED              | Optional | Forcebrute protection is disabled           | True                               |
| AXES_LOCK_OUT_AT_FAILURE  | Optional | Ban on forcebrute login                     | True                               |
| AXES_COOLOFF_TIME         | Optional | Ban duration on forcebrute login (in hours) | 0.8333                             |
| DONT_SERVES_STATIC_FILE   | Optional | Don't serve static files with django        | True                               |


## Sample deployment

Edit docker compose configuration (```docker-compose.yml```)

```yaml
version: '2'

services:
  front:
    image: atexio/mercure
    restart: always
    ports:
      - 8000:8000
    environment:
      SECRET_KEY: '<random value>'
      URL: 'https://preprod.mercure.io'
      EMAIL_HOST:  'mail.example.com'
      EMAIL_HOST_USER: 'phishing@example.com'
      EMAIL_HOST_PASSWORD: 'P@SSWORD'
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./data/database:/code/database
      - ./data/media:/code/media
      - ./data/migrations/phishing:/code/phishing/migrations

```

To generate the SECRET_KEY variable, you can use this command:

```shell
# generate random SECRET_KEY
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 200 | head -n 1
```

The SECRET_KEY is used as a salt for django password hashing, don't change it after using it with mercure.
After changing the secret key, you can run the container with this command:

```shell
docker-compose up -d
```

Next, you can create a super user to log into web interface:

```bash
# create super user
docker-compose exec front python manage.py createsuperuser
```

# How to use mercure

We can consider mercure is divided into 5 steps :
* Targets
* Email Templates
* Campaigns
* Attachments
* Landing page

Targets, Email Templates and Campaign are the minimum required to run a basic phishing campaign.


1. First, add your targets

   ![Targets](https://raw.githubusercontent.com/atexio/mercure/master/docs/img/mercure_targets.png)

   You need to fill mercure name, the target email.Target first and last name are optional, but can be usefull to the landing page

2. Then, fill the email template.

   ![Landing page](https://raw.githubusercontent.com/atexio/mercure/master/docs/img/mercure_emailtemplate.png)

   You need to fill the mercure name, the subject, the send and the email content.
   To improve the email quality, you have to fill the email content HTML and the text content.
   To get information about opened email, check "Add open email tracker"
   You can be helped with "Variables" category.

   Attachments and landing page are optionnal, we will see it after.

3. Finally, launch the campaign

   ![Campaign](https://raw.githubusercontent.com/atexio/mercure/master/docs/img/mercure_campaign.png)

   You need to fill the mercure name, select the email template and the target group.
   You can select the SMTP credentials, SSL using or URL minimazing


4. Optional, add landing page

   ![Landing page](https://raw.githubusercontent.com/atexio/mercure/master/docs/img/mercure_landingpage.png)

   You need to fill the mercure name, the domain to use
   You can use "Import from URL" to copy an existing website.

   You have to fill the page content with text and HTML content by clicking to "Source"

5. Optional, add Attachment

   ![Attachments](https://raw.githubusercontent.com/atexio/mercure/master/docs/img/mercure_attachment.png)

   You need to fill the mercure name, the file name which appears in the email and the file
   You also have to check if the the file is buildable or not, if you need to compute a file for example.

   To execute the build , you need to create a zip archive which contain a build script (named 'generator.sh' and a buildable file



# Developers

## To participate to the project :

1. Fork the project

2. Create new branch

3. Make comments and clean commits to the repository

4. Run unnittests
	```
	python manage.py test --exclude-tag selenium
	```

5. Perform a pull request


# Responsible Disclosure of Security Vulnerabilities

We want to keep Mercure safe for everyone. If you've discovered a security vulnerability in Mercure, we appreciate your help in disclosing it to us in a responsible manner.

Send an email to 'security@atexio.fr'. If you want, you can use with [PGP Key](https://pgp.mit.edu/pks/lookup?op=vindex&search=security@atexio.fr)


## Vulnerability summary

* Name of the vulnerability
* Attack Vector (AV)
* Attack Complexity (AC)
* Privileges Required (PR)
* User Interaction (UI)
* Scope (S)
* Confidentiality (C)
* Integrity (I)
* Availability (A)


## Reporter informations
* Your Name
* Your Mail
* Your PGP public key


## Technical details
* More technical details.
