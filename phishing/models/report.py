from django.db.models import ForeignKey
from django.db.models import Model, CharField


class Report(Model):
    title = CharField(max_length=250)
    campaign_id = ForeignKey('Campaign', related_name='report')

    def __str__(self):
        return self.title
