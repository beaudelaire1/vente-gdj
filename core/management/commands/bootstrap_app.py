from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from core.models import Customer, Event, Order, StatusLog


class Command(BaseCommand):
    help = "Prépare l'application pour le local ou la production (migrations, users, import de données)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--excel',
            type=str,
            help='Chemin vers un fichier Excel source à importer avec la commande import_excel',
        )
        parser.add_argument(
            '--json',
            type=str,
            help='Chemin vers un fichier JSON exporté à importer avec la commande import_data',
        )
        parser.add_argument(
            '--event-name',
            type=str,
            default='Restaurant Éphémère GDJ EEBC',
            help="Nom de l'événement à utiliser avec --excel",
        )
        parser.add_argument(
            '--event-date',
            type=str,
            default='2026-03-28',
            help="Date de l'événement à utiliser avec --excel (AAAA-MM-JJ)",
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Efface les données métier existantes avant import',
        )
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='N’exécute pas setup_users',
        )
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='N’exécute pas migrate',
        )

    def handle(self, *args, **options):
        excel_file = options.get('excel')
        json_file = options.get('json')
        clear_data = options.get('clear', False)

        if excel_file and json_file:
            raise CommandError('Utilisez soit --excel soit --json, pas les deux.')

        if clear_data and not (excel_file or json_file):
            raise CommandError('--clear nécessite --excel ou --json.')

        if not options.get('skip_migrate'):
            self.stdout.write('1. Application des migrations...')
            call_command('migrate', interactive=False)

        if not options.get('skip_users'):
            self.stdout.write('2. Création des utilisateurs par défaut...')
            call_command('setup_users')

        if clear_data:
            self.stdout.write('3. Nettoyage des données métier existantes...')
            self._clear_business_data()

        if excel_file:
            file_path = Path(excel_file)
            if not file_path.exists():
                raise CommandError(f'Fichier Excel introuvable : {excel_file}')
            self.stdout.write('4. Import des données Excel...')
            call_command(
                'import_excel',
                str(file_path),
                event_name=options['event_name'],
                event_date=options['event_date'],
            )
        elif json_file:
            file_path = Path(json_file)
            if not file_path.exists():
                raise CommandError(f'Fichier JSON introuvable : {json_file}')
            self.stdout.write('4. Import des données JSON...')
            call_command('import_data', file=str(file_path), clear=False)
        else:
            self.stdout.write('4. Aucun import demandé.')

        self.stdout.write(self.style.SUCCESS(self._build_summary()))

    def _clear_business_data(self):
        with transaction.atomic():
            StatusLog.objects.all().delete()
            Order.objects.all().delete()
            Customer.objects.all().delete()
            Event.objects.all().delete()

    def _build_summary(self):
        active_event = Event.objects.filter(is_active=True).values_list('name', flat=True).first()
        return (
            'Bootstrap terminé | '
            f"events={Event.objects.count()} | "
            f"customers={Customer.objects.count()} | "
            f"orders={Order.objects.count()} | "
            f"logs={StatusLog.objects.count()} | "
            f"active_event={active_event or 'aucun'}"
        )
