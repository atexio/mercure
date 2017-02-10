from django.dispatch import Signal


# Called on landing page before printed by target
landing_page_printed = Signal(providing_args=['request', 'landing_page'])
