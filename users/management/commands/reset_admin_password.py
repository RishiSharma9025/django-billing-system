import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Reset password for a user (by username). Use when you forgot the admin password. "
        "For superuser creation, use: python manage.py createsuperuser"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            nargs="?",
            help="Username whose password will be reset (prompted if omitted).",
        )
        parser.add_argument(
            "--superuser-only",
            action="store_true",
            help="Only allow resetting if the user is a superuser.",
        )

    def handle(self, *args, **options):
        username = (options.get("username") or "").strip()
        if not username:
            username = input("Username: ").strip()
        if not username:
            raise CommandError("Username is required.")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"No user with username '{username}'.") from exc

        if options["superuser_only"] and not user.is_superuser:
            raise CommandError(f"User '{username}' is not a superuser (use without --superuser-only to reset any user).")

        p1 = getpass.getpass("New password: ")
        p2 = getpass.getpass("New password (again): ")
        if p1 != p2:
            raise CommandError("Passwords do not match.")
        if not p1:
            raise CommandError("Password cannot be empty.")

        user.set_password(p1)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Password updated for '{username}'."))

