from rest_framework.throttling import UserRateThrottle


class PriceCheckThrottle(UserRateThrottle):
    """
    Throttle for price checking endpoint to prevent brute-force discount code attacks.

    Limits:
    - Authenticated users: 10 requests per minute
    - This prevents automated brute-force attempts while allowing legitimate use
    """

    scope = "price_check"
    rate = "10/min"

    def get_cache_key(self, request, view):
        """
        Custom cache key based on user ID for authenticated users.
        For anonymous users (shouldn't happen with auth required), use IP.
        """
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
