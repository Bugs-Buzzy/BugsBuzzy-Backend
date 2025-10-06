from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # We can leave this empty for now and add fields later,
    # or add our first custom field.
    team_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام تیم")

    def __str__(self):
        return self.username