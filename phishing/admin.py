from django.contrib import admin

from . import models

admin.site.register(models.Campaign)
admin.site.register(models.EmailTemplate)
admin.site.register(models.Target)
admin.site.register(models.TargetGroup)
admin.site.register(models.Tracker)
admin.site.register(models.TrackerInfos)
admin.site.register(models.User)
