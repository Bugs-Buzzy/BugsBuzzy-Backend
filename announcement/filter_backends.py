from typing import Dict, Any, Callable
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


# Minimal registry for backends: each must return a Django QuerySet
REGISTRY: Dict[str, Callable[[Dict[str, Any], Any], QuerySet]] = {}


def register(name: str):
    def _decorator(fn: Callable[[Dict[str, Any], Any], QuerySet]):
        REGISTRY[name] = fn
        return fn
    return _decorator


def get_backend(name: str):
    return REGISTRY.get(name)


@register('basic')
def basic_backend(params: Dict[str, Any], filter_instance):
    """Basic backend: read params keys for flags/email_domain/extra_q and return a QuerySet.

    Expected params example:
      {"flags": ["is_verified", "has_paid"], "email_domain": "example.com", "extra_q": "profile_completed=True"}
    """
    qs = User.objects.all()

    flags = params.get('flags') or []
    if isinstance(flags, str):
        flags = [f.strip() for f in flags.split(',') if f.strip()]
    for flag in flags:
        if hasattr(User, flag):
            qs = qs.filter(**{flag: True})

    email_domain = params.get('email_domain')
    if email_domain:
        qs = qs.filter(email__iendswith='@' + str(email_domain))

    extra_q = params.get('extra_q')
    if extra_q:
        try:
            k, v = str(extra_q).split('=')
            k = k.strip()
            v = v.strip()
            if v.lower() in ['true', 'false']:
                val = v.lower() == 'true'
            else:
                val = v
            qs = qs.filter(**{k: val})
        except Exception:
            pass

    return qs
