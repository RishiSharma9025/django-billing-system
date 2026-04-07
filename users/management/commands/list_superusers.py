from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print all users where is_superuser is True (Django auth User model)."

    def handle(self, *args, **options):
        qs = User.objects.filter(is_superuser=True).order_by("username")
        count = qs.count()
        self.stdout.write(self.style.SUCCESS(f"Superusers ({count}):"))
        for u in qs:
            email = u.email or "(no email)"
            self.stdout.write(f"  - {u.username}  |  {email}  |  active={u.is_active}")

