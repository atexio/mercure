import json

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, \
    PermissionRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DeleteView, UpdateView, CreateView, ListView

from mercure import settings
from phishing.helpers import clone_url, get_template_vars, intercept_html_post
from phishing.models import LandingPage, Tracker, TrackerInfos
from phishing.strings import TRACKER_LANDING_PAGE_POST, POST_TRACKER_ID, \
    POST_DOMAIN, TRACKER_ATTACHMENT_LP_EXECUTED
from phishing.signals import landing_page_printed


@permission_required('add_landingpage')
def clone(request):
    """Use to clone the html of any page."""
    url = request.POST.get('url')
    if not url:
        return HttpResponseBadRequest()

    # get html of utl
    html = clone_url(url)

    # add intercept post data
    html = intercept_html_post(html, url)

    return HttpResponse(html)


class Create(LoginRequiredMixin, CreateView):
    """Use to create landing page."""
    model = LandingPage
    success_url = reverse_lazy('landing_page_list')
    fields = ('name', 'domain', 'html', 'attachments')

    def get_context_data(self, **kwargs):
        ctx = super(Create, self).get_context_data(**kwargs)

        # add vars infos
        ctx['template_vars'] = get_template_vars()

        return ctx


class Edit(Create, UpdateView):
    """Use to edit landing page."""
    pass


class Delete(PermissionRequiredMixin, DeleteView):
    """Use to delete landing page."""
    model = LandingPage
    permission_required = 'del_campaign'
    success_url = reverse_lazy('landing_page_list')


def landing_page(request, tracker_id):
    """Show landing page.

    :param request:
    :param tracker_id:
    :return:
    """
    # add infos
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    tracker_infos = TrackerInfos.create(target_tracker=tracker,
                                        http_request=request)
    count = TrackerInfos.objects.filter(target_tracker=tracker).count()

    # update values
    tracker.value = 'opened'
    tracker.infos = count
    tracker.save()

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

    # return landing page
    try:
        campaign = tracker.campaign
        email_template = campaign.email_template
        landing_page = email_template.landing_page
        html = landing_page.html
        target = tracker.target

        for var in get_template_vars(campaign, target, email_template):
            html = html.replace(var['name'], var['value'] or '')

        # Loop on all attachments in landing_page
        for idx,attachment in enumerate(landing_page.attachments.all()):
            # Build attachment if necessary
            if attachment.buildable:
                tracker = add_tracker(TRACKER_ATTACHMENT_LP_EXECUTED,
                                      '%s: not executed' % attachment.name,
                                      0)
                attachment_file = attachment.build(tracker)
            else:
                attachment_file = attachment.file


            # Host the attachment on the server
            #     'filename': attachment.attachment_name,
            #     'content': attachment_file.read()

            # Replace the variable by the link
            # html = html.replace("{{ attachment_"+idx+1 }}, ###url### or '')

        # add navigator info script
        navigator_info = render_to_string(
            'phishing/landingpage_navigator_infos.html', {
                'tracker_id': tracker.pk,
            })
        html = html.replace('</body>', '%s</body>' % navigator_info)

        # replace the post tracker id
        if POST_TRACKER_ID in html:
            tracker_post = Tracker.objects.filter(
                campaign=campaign, target=target, key=TRACKER_LANDING_PAGE_POST
            ).first()

            if tracker_post:
                value = str(tracker_post.pk)
            else:
                value = 'unknown'
                tracker_infos.raw = 'tracker_post_id of %s in unknown' % \
                                    tracker_id
                tracker_infos.save()

            html = html.replace(POST_TRACKER_ID, value)

        # replace the landing page domain
        if POST_DOMAIN in html:
            landing_page_hostname = request.META.get('HTTP_HOST') or \
                settings.HOSTNAME.split('//', 1)[-1].split('/')[0]
            html = html.replace(POST_DOMAIN, landing_page_hostname)

        landing_page.html = html
        landing_page_printed.send(sender=request, request=request,
                                  landing_page=landing_page)

        return HttpResponse(landing_page.html, content_type='text/html')
    except Exception as e:
        tracker_infos.raw = '%s: %s' % (e.__class__.__name__, e)
        tracker_infos.save()
        return HttpResponseRedirect('https://www.google.com/')


@csrf_exempt
def landing_page_post(request, tracker_id):
    """Save landing page POST infos and redirect to true URL.

    :param request:
    :param tracker_id:
    :return:
    """
    # add infos
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    TrackerInfos.create(target_tracker=tracker, http_request=request,
                        raw=json.dumps(request.POST))
    count = TrackerInfos.objects.filter(target_tracker=tracker).count()

    # update values
    tracker.value = 'yes'
    tracker.infos = count
    tracker.save()

    # redirect to legitimate website
    post = request.POST.dict()
    return render(request, 'phishing/landingpage_post_redirect.html', {
        'action': post.pop('mercure_real_action_url'),
        'redirect_url': post.pop('mercure_redirect_url'),
        'post': post,
    })


class List(LoginRequiredMixin, ListView):
    model = LandingPage
