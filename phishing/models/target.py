from django.db.models import CASCADE, CharField, EmailField, ForeignKey, Model
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_rq import get_scheduler


class Target(Model):
    """
        People who'll be targeted

        :param email(EmailField): Target's email
        :param group(ForeignKey): Link to :func:`target group class
                                    <phishing.models.target.TargetGroup>`
        :param first_name(CharField): (Optional) First name of the target
        :param last_name(CharField): (Optional) Last name of the target
    """
    email = EmailField()
    group = ForeignKey('TargetGroup', on_delete=CASCADE,
                       related_name='targets')

    # optional infos
    first_name = CharField(max_length=128, blank=True)
    last_name = CharField(max_length=128, blank=True)

    def __str__(self):
        """
            Print function for Target
            :return text: Print the email of the target
        """
        return self.email


class TargetGroup(Model):
    """
        Group of people who'll be targeted

        :param name(CharField): Name of the target group in mercure interface

    """
    name = CharField(_('Staff category'), max_length=128)

    def __str__(self):
        """
            Print function for TargetGroup
            :return text: Print the name of the targetGroup
        """
        return self.name


@receiver(m2m_changed)
def handler(action, instance, model, **kwargs):
    """
        Send email on group added to campaign
        Handler campaign's start to send email
    """
    if action == 'post_add' and model == TargetGroup:
        from phishing.helpers import start_campaign
        get_scheduler().enqueue_at(instance.send_at, start_campaign, instance)
