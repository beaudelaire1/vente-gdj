from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = "Crée les utilisateurs par défaut avec leurs rôles"

    def handle(self, *args, **options):
        users_data = [
            ('admin', 'admin2026!', UserProfile.ROLE_ADMIN, True),
            ('caisse', 'caisse2026!', UserProfile.ROLE_CAISSE, False),
            ('preparation', 'prep2026!', UserProfile.ROLE_PREPARATION, False),
        ]

        for username, password, role, is_super in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'is_staff': is_super,
                    'is_superuser': is_super,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Utilisateur créé : {username} (mot de passe : {password})"
                ))
            else:
                self.stdout.write(f"Utilisateur existant : {username}")

            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': role},
            )
