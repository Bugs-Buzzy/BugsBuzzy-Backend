from __future__ import annotations

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .emails import send_user_announcement_email
from .models import UserAnnouncement

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserAnnouncement)
def send_user_announcement_when_created(
    sender, instance: UserAnnouncement, created: bool, **kwargs
):
    if not created:
        return

    def _send():
        try:
            send_user_announcement_email(instance)
        except Exception as exc:  # pragma: no cover - email backend dependent
            logger.exception("Failed to send announcement email on creation", exc_info=exc)

    transaction.on_commit(_send)
