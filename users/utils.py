from django.db.models import QuerySet

from .models import Business


def get_owner_business(user):
    """Return the Business for a normal owner user. None means \"no row\" or superuser/staff (see below)."""
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return None
    return user.businesses.order_by("-id").first()


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def queryset_for_business(model_qs: QuerySet, user, *, business_field: str = "business"):
    """
    Superuser/staff: full queryset.
    Owner: filter by their business FK.
    """
    if is_staff_or_superuser(user):
        return model_qs
    b = get_owner_business(user)
    if not b:
        return model_qs.none()
    return model_qs.filter(**{business_field: b})
