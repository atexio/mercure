import re

from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, \
    PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView
from django.views.generic import DeleteView

from phishing.models import Target
from ..helpers import to_hour_timestamp
from ..models import Campaign, Tracker, TrackerInfos
from phishing.signals import make_campaign_report


class CreateCampaign(PermissionRequiredMixin, CreateView):
    """Use to create campaign."""

    permission_required = 'add_campaign'
    model = Campaign
    fields = ('name', 'email_template', 'target_groups', 'send_at',
              'smtp_host', 'smtp_username', 'smtp_password', 'smtp_use_ssl',
              'minimize_url')
    success_url = reverse_lazy('campaign_list')

    def get_form(self, form_class=None):
        form = super(CreateCampaign, self).get_form(form_class)
        form.fields['smtp_use_ssl'].label = _('Use SSL')
        return form

    def form_valid(self, form):
        # get and remove target_groups infos (django crash if not manualy make)
        target_groups = form.cleaned_data.pop('target_groups', [])
        form.data = form.data.copy()
        form.data.pop('target_groups', [])
        form.fields.pop('target_groups', None)

        # save model
        result = super(CreateCampaign, self).form_valid(form)

        # add target_groups link
        for target_group in target_groups.all():
            self.object.target_groups_add(target_group)

        return result


@login_required
def dashboard(request, pk):
    """Show dashboard of campaign.

    :param request:
    :param pk:
    :return:
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    # If campaign is not launched we can't see the dashboard
    if not campaign.is_launched:
        raise Http404()

    graphs = {}
    targets_details = {}

    # last event timestamp
    last_event_datetime = Tracker.objects.filter(campaign_id=pk)\
        .order_by('updated_at').last().updated_at

    # generate empty value
    empty_values_histogram = {t: 0 for t in range(
        to_hour_timestamp(campaign.created_at),
        to_hour_timestamp(last_event_datetime) + 3601,
        3600
    )}

    # at least one day
    while True:
        if len(empty_values_histogram) > 24:
            break
        empty_values_histogram[min(list(empty_values_histogram)) - 3600] = 0

    def add_histogram_value(name, datetime, value):
        """Add value to histogram graph.

        :param name: graph name
        :param datetime: datetime event
        :param value: value name (category)
        """
        graph_name = '%s_histogram' % name

        if graph_name not in graphs:
            graphs[graph_name] = {}

        # init histogram empty point
        if value not in graphs[graph_name]:
            graphs[graph_name][value] = empty_values_histogram.copy()

        # add value
        graphs[graph_name][value][to_hour_timestamp(datetime)] += 1

    def add_pie_value(name, value, fixed_color=''):
        """Add value to pie graph.

        :param name: graph name
        :param value: value name (category)
        """
        graph_name = '%s_pie' % name

        if graph_name not in graphs:
            graphs[graph_name] = {}

        if value not in graphs[graph_name]:
            graphs[graph_name][value] = {
                'value': 0,
                'color': fixed_color,
            }

        graphs[graph_name][value]['value'] += 1

    def clean_name(name):
        return re.sub('[^0-9a-zA-Z]+', '_', name)

    # generate tracker graph
    for tracker in Tracker.objects.filter(campaign_id=pk) \
            .order_by('created_at'):  # order column (in user details)
        # init targets details
        if tracker.target_id not in targets_details:
            targets_details[tracker.target_id] = OrderedDict({
                'email': tracker.target.email,
            })
        # add values
        key = clean_name(tracker.key)
        targets_details[tracker.target_id][tracker.key] = tracker
        value = '%s (%s)' % (tracker.key, tracker.value)
        unchanged_value = (
              tracker.updated_at - tracker.created_at).total_seconds() < 1
        pie_color_value = '#bdc3c7' if unchanged_value else '#e67e22'

        add_pie_value(key, value, pie_color_value)
        add_histogram_value(key, tracker.updated_at, value)

        # can has trakerInfos entry ?
        if key != 'email_send':
            # add to count values
            try:
                count = int(tracker.infos)
            except TypeError:
                count = 0

            val = '%s_%s_tracker_count' % (key, clean_name(tracker.value))
            graphs[val] = count

            val_count = '%s_tracker_count' % key
            graphs[val_count] = count + graphs.get('%s_count' % key, 0)

        else:
            # add unique entry on global histogram
            add_histogram_value('all', tracker.updated_at, value)

        # generate target group graph
        if campaign.target_groups.count() > 1:
            try:
                count = int(tracker.infos)
                name = 'target_group_%s' % key

                # search all user group (in current campaign)
                groups = []
                for t in Target.objects.filter(email=tracker.target.email):
                    if t.group in campaign.target_groups.all():
                        groups.append(t.group)

                # add value on user's group
                for group in groups:
                    # increase pie counter
                    for i in range(count):
                        add_pie_value(name, group.name)

            except (TypeError, ValueError):
                # has not value (integer cast error)
                pass

    # generate tracker infos graph
    for tracker in TrackerInfos.objects.filter(
            target_tracker__campaign=campaign).order_by('-created_at'):
        # get values
        target_tracker = tracker.target_tracker
        name = clean_name('%s_infos' % target_tracker.key)
        value = '%s (%s)' % (target_tracker.key, target_tracker.value)

        # add values
        add_pie_value(name, value)
        add_histogram_value('all', tracker.created_at, value)
        add_histogram_value(name, tracker.created_at, value)

        # add target graph
        name = 'target_%s' % tracker.target_tracker.target_id
        value = '%s (%s)' % (tracker.target_tracker.key,
                             tracker.target_tracker.value)
        add_histogram_value(name, tracker.created_at, value)

    # init tracker infos graph (if empty graph)
    for index in graphs.copy():
        name = '_infos_'.join(index.rsplit('_', 1))

        if name in graphs:  # ignore if graph exist (has value)
            continue

        if name.endswith('_pie'):
            graphs[name] = {i: 0 for i in graphs[index]}

        if name.endswith('_histogram'):
            graphs[name] = {i: empty_values_histogram for i in graphs[index]}

    # init graph layout
    tabs_layout = OrderedDict()
    tabs_layout['Global'] = ['global.html', 'email_open.html',
                             'landing_page.html', 'attachment.html']

    # add target group graph
    if campaign.target_groups.count() > 1:
        tabs_layout['Global'].append('target_group.html')

    # if staff => more details (annonimized for client account)
    if request.user.is_superuser:
        tabs_layout['Users details'] = ['targets_details.html']

    tabs_layout['Other'] = ['campaign_infos.html']

    context = {
        'graphs': graphs,
        'campaign': campaign,
        'tabs_layout': tabs_layout,
        'targets_details': targets_details,
    }

    # call modules handler
    make_campaign_report.send(sender=Campaign, context=context,
                              campaign=campaign)
    return render(request, 'phishing/campaign_dashboard.html', context)


class Delete(PermissionRequiredMixin, DeleteView):
    """Use to delete campaign."""
    model = Campaign
    permission_required = 'del_campaign'
    success_url = reverse_lazy('campaign_list')


class ListCampaign(LoginRequiredMixin, ListView):
    """Use to create campaign"""
    model = Campaign
