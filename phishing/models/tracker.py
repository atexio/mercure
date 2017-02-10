from uuid import uuid4

from django.db.models import CASCADE, CharField, DateTimeField, ForeignKey, \
    GenericIPAddressField, Model, TextField, UUIDField


class Tracker(Model):
    """
        Target statistics for one campaign.
        Contain usefull infos from the campaign

        :param uuid(UUIDField): Unique id to identify the tracker
        :param campaign(ForeignKey): Link to :func:`campaign class
                                        <phishing.models.campaign.Campaign>`
        :param target(ForeignKey): Link to :func:`target class
                                        <phishing.models.target.Target>`
        :param created_at(DateTimeField): Date of tracker's creation
        :param updated_at(DateTimeField): Date of tracker's update
        :param key(CharField): Tracker's type (for developer)
        :param value(CharField): Tracker's value (for mercure's user, to get
                                                tracker's status)
        :param infos(TextField): Summary of all the tracker's info
    """
    uuid = UUIDField(unique=True, primary_key=True, default=uuid4)
    campaign = ForeignKey('Campaign', on_delete=CASCADE,
                          related_name='trackers')
    target = ForeignKey('Target', on_delete=CASCADE,
                        related_name='trackers')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    key = CharField(max_length=128)
    value = CharField(max_length=255)
    infos = TextField(blank=True, null=True)

    def __str__(self):
        """
            Print function for Tracker
            :return text: Print tracker's information (not all the infos)
        """
        return '[%s] %s (%s: %s)' % (self.campaign, self.target, self.key,
                                     self.value)

    class Meta:
        ordering = ['-updated_at']


class TrackerInfos(Model):
    """
        Contain all the infos entry for target tracker.

        :param target_tracker(ForeignKey): Link to :func:`tracker class
                                            <phishing.models.tracker.Tracker>`
        :param created_at(DateTimeField): Date of tracker's creation
        :param ip(GenericIPAddressField): Get the target's IP
        :param raw(TextField): Raw data (contains more information)
        :param referer(TextField): Referer web if target open the email
                                            with web browser
        :param user_agent(TextField): Get the target's user_agent
    """
    target_tracker = ForeignKey('Tracker', related_name='tracker_infos',
                                on_delete=CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    ip = GenericIPAddressField(blank=True, null=True)
    raw = TextField(blank=True, null=True)
    referer = TextField(blank=True, null=True)
    user_agent = TextField(blank=True, null=True)

    def __str__(self):
        """
            Print function for TrackerInfos
            :return text: Print tracker's information (not all the infos)
        """
        return str(self.target_tracker)

    @classmethod
    def create(cls, http_request=None, **kwargs):
        """
            Create info entry (for a target tracker)

            :param http_request: django http request object
            :param kwargs: optional value to pass to constructor
            :return: TrackerInfos created object
        """

        # extract standard info to http request
        if http_request:
            meta = http_request.META
            kwargs['user_agent'] = meta.get('HTTP_USER_AGENT')
            kwargs['referer'] = meta.get('HTTP_REFERER')
            forward_ip = meta.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
            kwargs['ip'] = forward_ip or meta.get('REMOTE_ADDR')

        return cls.objects.create(**kwargs)

    class Meta:
        ordering = ['-created_at']
