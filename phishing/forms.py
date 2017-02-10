from django.forms import ModelForm, inlineformset_factory

from .models import Target, TargetGroup


class TargetForm(ModelForm):
    """Form to add targets"""
    class Meta:
        model = Target
        fields = ('email', 'first_name', 'last_name')


TargetFormset = inlineformset_factory(TargetGroup, Target,
                                      form=TargetForm, extra=1)
