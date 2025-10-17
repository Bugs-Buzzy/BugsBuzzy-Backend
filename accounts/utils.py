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
        
        subject = "Email Verification - BugsBuzzy"
        
        context = {
            'verification_code': verification_code_str,
            'recipient_email': recipient_email
        }
        
        html_body = render_to_string('emails/verification_email.html', context)
        
        send_mail(
            subject=subject,
            message=f"Your verification code is: {verification_code_str}",
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


def send_email(to_address, subject, body):
    """
    Send email using SMTP
    """
    try:
        # Get email settings from environment or use defaults
        smtp_server = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("EMAIL_PORT", "587"))
        email_username = os.environ.get("EMAIL_HOST_USER")
        email_password = os.environ.get("EMAIL_HOST_PASSWORD")
        from_email = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@bugsbuzzy.com")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_address
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'html'))
        
        # Create SMTP session
        if smtp_port == 465:
            # SSL connection
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            # TLS connection
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        # Login and send email
        if email_username and email_password:
            server.login(email_username, email_password)
        
        server.sendmail(from_email, to_address, msg.as_string())
        server.quit()
        
        print(f"Email sent successfully to {to_address}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
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
