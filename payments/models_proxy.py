from django.contrib.auth import get_user_model

User = get_user_model()


class UserPurchasesSummary(User):
    """Proxy model to show user purchases summary in admin"""

    class Meta:
        proxy = True
        verbose_name = "User Purchases Summary"
        verbose_name_plural = "Users Purchases Summary"
