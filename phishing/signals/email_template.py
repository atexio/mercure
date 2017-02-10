from django.dispatch import Signal


# Called on template variables list create
make_template_vars = Signal(providing_args=['vars_data', 'campaign', 'target',
                                            'email_template'])
