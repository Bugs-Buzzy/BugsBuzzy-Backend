from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from .utils import normalize_email


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        # Only set normalized_email if not already provided
        if "normalized_email" not in extra_fields:
            extra_fields["normalized_email"] = normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    STATUS_CHOICES = [
        ("verified", "Verified"),
        ("pending_verification", "Pending Verification"),
    ]

    username = None
    first_name = models.CharField(max_length=50, verbose_name="First Name")
    last_name = models.CharField(max_length=50, verbose_name="Last Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    normalized_email = models.EmailField(
        max_length=255, unique=True, null=True, blank=True, verbose_name="Normalized Email"
    )

    national_code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(regex=r"^\d{10}$", message="National code must be exactly 10 digits")
        ],
        verbose_name="National Code",
    )
    phone_number = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$", message="Phone number must start with 09 and be 11 digits"
            )
        ],
        verbose_name="Phone Number",
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Gender")
    birth_date = models.DateField(null=True, verbose_name="Birth Date")
    city = models.CharField(max_length=100, verbose_name="City", default="")
    university = models.CharField(max_length=100, verbose_name="University", default="")
    major = models.CharField(max_length=100, verbose_name="Major", default="")

    is_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending_verification", verbose_name="Status"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    last_login_ip = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Last Login IP"
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Email Verified At"
    )

    verification_code = models.PositiveIntegerField(
        validators=[MinValueValidator(100000), MaxValueValidator(999999)],
        null=True,
        blank=True,
        verbose_name="Verification Code",
    )
    code_updated_at = models.DateTimeField(
        default=timezone.now, null=False, blank=False, verbose_name="Code Updated At"
    )
    try_count = models.PositiveIntegerField(default=0, verbose_name="Verification Try Count")

    has_paid = models.BooleanField(default=False, null=False, verbose_name="Has Paid")
    profile_completed = models.BooleanField(default=False, verbose_name="Profile Completed")

    USERNAME_FIELD = "normalized_email"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return self.email
