from django.dispatch import Signal


# Called to make user menu
make_menu = Signal(providing_args=['urls'])
