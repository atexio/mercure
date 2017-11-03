from django.test import TestCase
from django_rq import get_connection, get_scheduler, get_queue


class RQTestCase(TestCase):
    def setUp(self):
        super(RQTestCase, self).setUp()
        get_connection().flushdb()
        self.scheduler = get_scheduler()

    def tearDown(self):
        super(RQTestCase, self).tearDown()
        get_connection().flushdb()

    def run_jobs(self):
        self.scheduler.run(burst=True)
        for job in get_queue().jobs:
            get_queue().run_job(job)