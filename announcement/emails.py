from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from markdown import markdown

from .models import UserAnnouncement

if TYPE_CHECKING:  # pragma: no cover
    from .models import Announcement

logger = logging.getLogger(__name__)

MARKDOWN_EXTENSIONS = [
    "extra",
    "sane_lists",
    "smarty",
]


def _render_markdown(description: Optional[str]) -> str:
    if not description:
        return ""
    return markdown(description, extensions=MARKDOWN_EXTENSIONS, output_format="html5")


def render_announcement_html(announcement: "Announcement") -> str:
    """Render the announcement description to safe HTML using Markdown."""

    html = _render_markdown(announcement.description)
    return mark_safe(html)  # nosec - content authored by trusted staff


def build_email_subject(announcement: "Announcement") -> str:
    return f"اطلاعیه: {announcement.title}" if announcement.title else "اطلاعیه جدید"


def send_user_announcement_email(
    user_announcement: UserAnnouncement, *, force: bool = False
) -> bool:
    """
    Send the announcement email to a specific user.

    Returns True if a send was attempted (and succeeded), False otherwise.
    Raises the underlying email exception if sending fails.
    """

    user = user_announcement.user
    if not getattr(user, "email", None):
        logger.warning("Skipping announcement email for user %s: no email set", user.pk)
        return False

    if user_announcement.email_sent_at and not force:
        return False

    announcement = user_announcement.announcement
    html_body = render_announcement_html(announcement)
    context = {
        "announcement": announcement,
        "announcement_body_html": html_body,
        "announcement_body_text": strip_tags(html_body),
        "user": user,
        "user_name": getattr(user, "get_full_name", lambda: "")()
        or getattr(user, "full_name", None)
        or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        or user.email,
    }

    email_subject = build_email_subject(announcement)
    html_message = render_to_string("emails/announcement_email.html", context)
    text_message = strip_tags(html_message)

    from_email = getattr(settings, "ANNOUNCEMENT_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)
    message = EmailMultiAlternatives(
        subject=email_subject,
        body=text_message,
        from_email=from_email,
        to=[user.email],
    )
    message.attach_alternative(html_message, "text/html")

    attempt_number = user_announcement.email_send_attempts + 1
    now = timezone.now()

    try:
        message.send()
    except Exception as exc:  # pragma: no cover - email backend dependent
        logger.exception("Failed to send announcement email", exc_info=exc)
        UserAnnouncement.objects.filter(pk=user_announcement.pk).update(
            email_send_attempts=attempt_number,
            email_last_error=str(exc),
        )
        user_announcement.email_send_attempts = attempt_number
        user_announcement.email_last_error = str(exc)
        raise

    UserAnnouncement.objects.filter(pk=user_announcement.pk).update(
        email_sent_at=now,
        email_delivered_at=now,
        email_send_attempts=attempt_number,
        email_last_error="",
    )
    user_announcement.email_sent_at = now
    user_announcement.email_delivered_at = now
    user_announcement.email_send_attempts = attempt_number
    user_announcement.email_last_error = ""

    return True
