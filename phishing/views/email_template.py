from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic import DeleteView

from ..helpers import get_template_vars
from ..models import EmailTemplate


class CreateEmailTemplate(PermissionRequiredMixin, CreateView):
    """Use to create email template."""
    permission_required = 'add_emailtemplate'
    model = EmailTemplate
    fields = ('name', 'email_subject', 'from_email', 'landing_page',
              'attachments', 'has_open_tracker', 'text_content',
              'html_content')
    success_url = reverse_lazy('email_template_list')

    def get_context_data(self, **kwargs):
        ctx = super(CreateEmailTemplate, self).get_context_data(**kwargs)

        # split on 2 form
        ctx['global_form'] = []
        ctx['textarea_form'] = []

        for field in list(ctx['form']):
            if field.html_name.endswith('_content'):
                ctx['textarea_form'].append(field)
            else:
                ctx['global_form'].append(field)

        # add vars infos
        ctx['template_vars'] = get_template_vars()

        return ctx


class EditEmailTemplate(CreateEmailTemplate, UpdateView):
    """Use to edit email template."""
    permission_required = 'change_emailtemplate'


class Delete(PermissionRequiredMixin, DeleteView):
    """Use to delete email template."""
    model = EmailTemplate
    permission_required = 'del_campaign'
    success_url = reverse_lazy('email_template_list')


class ListEmailTemplate(PermissionRequiredMixin, ListView):
    """Use to create list template."""
    permission_required = 'view_emailtemplate'
    model = EmailTemplate


@permission_required('add_emailtemplate')
def clone_email_template(request, pk):
    """Clone an email template.

    :param request:
    :param pk:
    :return:
    """
    obj = get_object_or_404(EmailTemplate, pk=pk)
    obj.pk = None
    obj.name = '[Clone] %s' % obj.name
    obj.save()

    return HttpResponseRedirect(reverse('email_template_list'))
