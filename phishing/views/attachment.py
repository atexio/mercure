from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView

from phishing.models import Attachment


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
