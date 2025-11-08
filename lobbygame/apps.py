from django.apps import AppConfig


class LobbygameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lobbygame"
    verbose_name = "Lobby Game"

    def ready(self):
        from django.db.utils import OperationalError
        from .models import LobbygameResult
        try:
            # Ensure the initial status row exists
            if not LobbygameResult.objects.filter(request_uuid="status").exists():
                LobbygameResult.objects.create(
                    request_uuid="status",
                    description="not started",
                )
        except OperationalError:
            # Skip if database not ready (e.g., during migrate)
            pass
