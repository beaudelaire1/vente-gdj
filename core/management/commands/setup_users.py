import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = "Crée les utilisateurs par défaut avec leurs rôles"

    def handle(self, *args, **options):
        users_data = [
            self._build_user_config(
                env_prefix='ADMIN',
                default_username='admin',
                default_password='admin2026!',
                role=UserProfile.ROLE_ADMIN,
                is_super=True,
            ),
            self._build_user_config(
                env_prefix='CAISSE',
                default_username='caisse',
                default_password='caisse2026!',
                role=UserProfile.ROLE_CAISSE,
                is_super=False,
            ),
            self._build_user_config(
                env_prefix='PREPARATION',
                default_username='preparation',
                default_password='prep2026!',
                role=UserProfile.ROLE_PREPARATION,
                is_super=False,
            ),
        ]

        for user_data in users_data:
            username = user_data['username']
            password = user_data['password']
            role = user_data['role']
            is_super = user_data['is_super']

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'is_staff': is_super,
                    'is_superuser': is_super,
                },
            )

            user.is_staff = is_super
            user.is_superuser = is_super
            user.set_password(password)
            user.save()

            action = 'créé' if created else 'mis à jour'
            self.stdout.write(self.style.SUCCESS(
                f"Utilisateur {action} : {username}"
            ))

            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': role},
            )
            if profile.role != role:
                profile.role = role
                profile.save(update_fields=['role'])

            profile_action = 'créé' if profile_created else 'synchronisé'
            self.stdout.write(f"Profil {profile_action} : {username} -> {role}")

    def _build_user_config(self, env_prefix, default_username, default_password, role, is_super):
        username = os.environ.get(f'DEFAULT_{env_prefix}_USERNAME', default_username)
        password = os.environ.get(f'DEFAULT_{env_prefix}_PASSWORD')

        if not password:
            if settings.DEBUG:
                password = default_password
            else:
                raise CommandError(
                    f"Variable d'environnement DEFAULT_{env_prefix}_PASSWORD manquante."
                )

        return {
            'username': username,
            'password': password,
            'role': role,
            'is_super': is_super,
        }
