from django.apps import AppConfig


class AnnouncementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "announcement"

    def ready(self):
        # Import signals to ensure they are registered when the app is ready
        from . import signals  # noqa: F401
