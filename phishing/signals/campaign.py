from django.dispatch import Signal


# Called before send email to target
send_email = Signal(providing_args=[
    'campaign', 'target', 'email_template', 'smtp_connection', 'attachments'])


# Called to make campaign report
make_campaign_report = Signal(providing_args=['context', 'campaign'])
