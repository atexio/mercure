from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView

from phishing.models import Attachment, Tracker, TrackerInfos


class CreateAttachment(PermissionRequiredMixin, CreateView):
    """Use to add attachments."""
    permission_required = 'add_attachment'
    model = Attachment
    fields = ('name', 'attachment_name', 'file', 'buildable')
    success_url = reverse_lazy('attachment_list')


class UpdateAttachment(CreateAttachment, UpdateView):
    """Use to edit attachments."""
    permission_required = 'change_attachment'


class DeleteAttachment(PermissionRequiredMixin, DeleteView):
    """Use to delete attachments."""

    permission_required = 'del_attachment'
    model = Attachment
    success_url = reverse_lazy('attachment_list')


class ListAttachment(PermissionRequiredMixin, ListView):
    """Use to list attachments."""

    permission_required = 'view_emailtemplate'
    model = Attachment


def download(request, attachment_id, tracker_id):
    # add infos
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    infos = TrackerInfos.create(target_tracker=tracker,
                                      http_request=request)
    count = TrackerInfos.objects.filter(target_tracker=tracker).count()

    # update values
    tracker.value = 'downloaded'
    tracker.infos = count
    tracker.save()


    attachment = get_object_or_404(Attachment, pk=attachment_id)
    attachment_file = attachment.build(tracker_id)
    response = HttpResponse(attachment_file,
                            content_type='application/force-download')
    response['Content-Disposition']= 'attachment; filename=%s' % \
                                     attachment.attachment_name
    return response

