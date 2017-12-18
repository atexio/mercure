from django.views.generic import DeleteView

from ..models import TargetGroup
from ..forms import TargetFormset
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView


class CreateTargetGroup(PermissionRequiredMixin, CreateView):
    """Use to create target group."""
    permission_required = 'add_targetgroup'
    model = TargetGroup
    fields = ('name',)
    success_url = reverse_lazy('target_group_list')

    def get_context_data(self, **kwargs):
        ctx = super(CreateTargetGroup, self).get_context_data(**kwargs)

        kwargs = {}
        if self.request.POST:
            kwargs['data'] = self.request.POST

        if self.object:
            kwargs['instance'] = self.object

        ctx['inlines'] = TargetFormset(**kwargs)
        return ctx

    def form_valid(self, form):
        inlines = self.get_context_data().get('inlines')
        if not inlines.is_valid():
            return self.form_invalid(form)

        res = super(CreateTargetGroup, self).form_valid(form)
        inlines.instance = self.object
        inlines.save()

        return res


class EditTargetGroup(CreateTargetGroup, UpdateView):
    """Use to edit target group."""
    permission_required = 'change_targetgroup'


class Delete(PermissionRequiredMixin, DeleteView):
    """Use to delete target group."""
    model = TargetGroup
    permission_required = 'del_campaign'
    success_url = reverse_lazy('target_group_list')


class ListTargetGroup(PermissionRequiredMixin, ListView):
    """Use to list target group."""
    permission_required = 'view_targetgroup'
    model = TargetGroup
