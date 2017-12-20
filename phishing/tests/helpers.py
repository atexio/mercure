from django_rq import get_connection, get_scheduler, get_queue


class RQMixin(object):
    def setUp(self):
        super(RQMixin, self).setUp()
        get_connection().flushdb()
        self.scheduler = get_scheduler()

    def tearDown(self):
        super(RQMixin, self).tearDown()
        get_connection().flushdb()

    def run_jobs(self):
        self.scheduler.run(burst=True)
        for job in get_queue().jobs:
            get_queue().run_job(job)
