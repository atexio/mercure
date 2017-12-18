#!/usr/bin/env python
import os
import sys


# Monkey patch for alpine
if os.path.isfile('/etc/alpine-release'):
    import threading
    threading.stack_size(100000)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mercure.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
