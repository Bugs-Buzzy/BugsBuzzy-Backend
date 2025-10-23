import smtplib
import ssl
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings


def send_verification_email(recipient_email, verification_code):
    """
    Send verification email to user with verification code using Django template
    """
    try:
        verification_code_str = str(verification_code).zfill(6)
        subject = "تأیید ایمیل - باگزبازی"
        context = {"verification_code": verification_code_str, "recipient_email": recipient_email}
        html_body = render_to_string("emails/verification_email.html", context)

        send_mail(
            subject=subject,
            message=f"کد تأیید شما: {verification_code_str}",
            html_message=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        print(f"Verification email sent to {recipient_email}")
        return True

    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False


def generate_verification_code():
    """
    Generate a 6-digit verification code
    """
    return random.randint(100000, 999999)


def normalize_email(email):
    """
    Normalize email address (lowercase, strip whitespace)
    """
    return email.lower().strip()


def validate_national_code(value):
    if len(value) != 10 or not value.isdigit():
        return False

    national_code = int(value)
    control = national_code % 10
    national_code //= 10

    sum_ = 0
    for i in range(2, 11):
        digit = national_code % 10
        sum_ += digit * i
        national_code //= 10

    remainder = sum_ % 11
    new_control = remainder if remainder < 2 else 11 - remainder

    return new_control == control
