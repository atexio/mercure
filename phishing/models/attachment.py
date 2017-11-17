import os
import tempfile
import zipfile
from base64 import b64decode
from io import BytesIO
from subprocess import check_output

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db.models import BooleanField, CharField, FileField, Model
from django.urls import reverse


class Attachment(Model):
    """
        Use for file's attachment in email template

        :param name (CharField): Name of the attachment in mercure interface
        :param attachment_name (CharField): Name of the attachment in the email
        :param file(FileField): Attachment file
        :param buildable(BooleanField): Boolean to know if file is buildable
    """
    name = CharField(max_length=128)
    attachment_name = CharField(max_length=128)
    file = FileField(upload_to='attachments')
    buildable = BooleanField()

    def __str__(self):
        """
            Print function for attachments
            :return text: Print the name of attachments
        """
        return self.name

    def build(self, tracker):
        """
            Use for build file's attachment if it's buildable
            :param tracker: Allow to know if user open/execute the attachment
            :return binary: Build of the file
        """
        if not self.buildable:
            return self.file

        with tempfile.TemporaryDirectory() as path:
            zipfile.ZipFile(self.file.path).extractall(path)
            builder_path = os.path.join(path, 'generator.sh')
            if not os.path.exists(builder_path):
                raise SuspiciousOperation('Unable to find builder script')

            # get values
            tracker_id = str(tracker.pk)
            target = tracker.target
            hostname = settings.HOSTNAME[:-1] if \
                settings.HOSTNAME.endswith('/') else settings.HOSTNAME
            tracker_url = hostname + reverse('tracker_img', args=(tracker_id,))

            # make env vars
            env = os.environ.copy()
            env.update({
                'TRACKER_URL': tracker_url,
                'TARGET_EMAIL': target.email,
                'TARGET_FIRST_NAME': target.first_name,
                'TARGET_LAST_NAME': target.last_name,
            })

            # TODO: Find a way to handle this RCE ;)
            cmd = ['sh', builder_path]
            out_b64 = check_output(cmd, cwd=path, env=env).decode().strip()
            return BytesIO(b64decode(out_b64))
