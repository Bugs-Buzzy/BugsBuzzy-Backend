from django.db import models


class Workshop(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    start_datetime = models.DateTimeField()
    duration = models.PositiveIntegerField()   # In Minutes

    presenter = models.CharField(max_length=255, null=True, blank=True)
    presenter_image = models.URLField(null=True, blank=True)

    vc_link = models.URLField(blank=True)   # For Online
    place = models.CharField(max_length=255, blank=True)   # For In-Person
    record_link = models.URLField(blank=True)   # For Recorded
