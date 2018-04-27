import cchardet
from datetime import datetime

import bs4 as BeautifulSoup
import requests
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from pyshorteners import Shortener

from mercure.settings import HOSTNAME
from phishing.signals import make_template_vars
from phishing.strings import TRACKER_LANDING_PAGE_OPEN, POST_TRACKER_ID, \
    POST_DOMAIN


def clone_url(url):
    """Get http code of url.

    :param url: url to clone
    :return:
    """
    # get html
    if '://' not in url:
        url = 'http://' + url

    r = requests.get(url)
    # We don't trust requests encoding so we use cchardet
    # to detect real encoding
    # Without it we got decode error (for example: baidu.com)
    r.encoding = cchardet.detect(r.content)['encoding']
    html = r.content.decode(r.encoding)

    # set relative url rule
    if '<base' not in html:
        html = html.replace('<head>', '<head><base href="%s" />' % url)

    return html


def get_template_vars(campaign=None, target=None, email_template=None):
    """Get template variable infos.

    :param campaign: `.models.Campaign`
    :param target: `.models.Target`
    :param email_template: `.models.EmailTemplate`
    :return: template variable infos
    """
    from .models import EmailTemplate, Tracker

    landing_page_url = ''

    # has landing page ?
    if email_template and email_template.landing_page:
        tracker = Tracker.objects.filter(
            campaign=campaign,
            target=target,
            key=TRACKER_LANDING_PAGE_OPEN
        ).first()

        if tracker:
            landing_page_url = '%s%s' % (
                email_template.landing_page.domain or HOSTNAME,
                reverse('landing_page', args=[tracker.pk])
            )

    # minimize urls
    if campaign and campaign.minimize_url:
        landing_page_url = minimize_url(landing_page_url)

    vars_data = [
        {
            'name': 'email',
            'description': _('Target email'),
            'value': target.email if target else ''
        },
        {
            'name': 'first_name',
            'description': _('Target first name'),
            'value': target.first_name if target else ''
        },
        {
            'name': 'last_name',
            'description': _('Target last name'),
            'value': target.last_name if target else ''
        },
        {
            'name': 'email_subject',
            'description': _('Current email subject'),
            'value': email_template.email_subject if email_template else ''
        },
        {
            'name': 'from_email',
            'description': _('Current from email'),
            'value': email_template.from_email if email_template else ''
        },
        {
            'name': 'date',
            'description': _('Current date in format DD/MM/YYYY'),
            'value': datetime.now().strftime('%d/%m/%Y'),
        },
        {
            'name': 'time',
            'description': _('Current time in format HH:MM'),
            'value': datetime.now().strftime('%H:%M'),
        },
        {
            'name': 'landing_page_url',
            'description': _('Url of landing page'),
            'value': landing_page_url,
        }
    ]

    make_template_vars.send(sender=EmailTemplate, vars_data=vars_data,
                            campaign=campaign, target=target,
                            email_template=email_template)
    return vars_data


def intercept_html_post(html, redirect_url=None):
    """Edit form to intercept posted data

    :param html: html page code
    :param redirect_url: url to redirect post
    :param is_secure: use https ?
    :return: edited html page code
    """
    soup = BeautifulSoup.BeautifulSoup(html, 'html5lib')
    hostname_url = '/'.join(
        redirect_url.split('/')[:3]) if redirect_url else ''

    # replace form
    for form in soup.find_all('form'):
        action = form.get('action', '')

        if redirect_url:
            # special url
            if action == '.':
                action = redirect_url

            elif action == '/':
                action = hostname_url

            elif action.startswith('/'):
                action = hostname_url + action

        # add action url in input hidden
        if 'action' not in form or POST_DOMAIN not in form['action']:
            form['action'] = 'http%s://%s%s' % (
                's' if HOSTNAME.startswith('https') else '',
                POST_DOMAIN,
                reverse('landing_page_post', args=[POST_TRACKER_ID]),
            )

        # add real action url
        if not form.find('input', {'name': 'mercure_real_action_url'}):
            input = soup.new_tag('input', type='hidden', value=action)
            input['name'] = 'mercure_real_action_url'
            form.append(input)

        # add redirect url
        if not form.find('input', {'name': 'mercure_redirect_url'}):
            value = redirect_url or form['action']
            input = soup.new_tag('input', type='hidden', value=value)
            input['name'] = 'mercure_redirect_url'
            form.append(input)

    return str(soup)


def minimize_url(url):
    """Minimise url

    :param url: url to minimize
    :return: url minimized
    """
    return Shortener('Tinyurl', timeout=10.0).short(url) if url else ''


def replace_template_vars(template, campaign=None, target=None,
                          email_template=None):
    """Replace vars in template

    :param template: template content
    :param campaign: `.models.Campaign`
    :param target: `.models.Target`
    :param email_template: `.models.EmailTemplate`
    :return: content with value
    """
    for var in get_template_vars(campaign, target, email_template):
        names = (
            '{{%s}}' % var['name'],
            '{{ %s }}' % var['name']
        )
        value = var['value'] or ''
        for name in names:
            template = template.replace(name, value)

    return template


def to_hour_timestamp(datetime):
    """Get timestamp (without minutes and second)

    :param datetime: datetime object
    :return: timestamp
    """
    return int(datetime.timestamp() / 3600) * 3600
