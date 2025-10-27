from rest_framework.throttling import AnonRateThrottle


class CheckEmailThrottle(AnonRateThrottle):
    """
    Throttle for check-email endpoint to prevent abuse.

    Limits:
    - 3 requests per minute per IP address
    - Prevents automated enumeration attacks while allowing legitimate use
    - Works correctly behind nginx proxy by reading X-Forwarded-For header
    """

    scope = "check_email"
    rate = "3/min"

    def get_ident(self, request):
        """
        Get real IP address from X-Forwarded-For header when behind nginx.
        Falls back to REMOTE_ADDR if header is not present.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            # X-Forwarded-For can contain multiple IPs, get the first one (client IP)
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def get_cache_key(self, request, view):
        """
        Custom cache key based on IP address for anonymous users.
        """
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
