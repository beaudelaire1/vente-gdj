from decimal import Decimal
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def recupere_to_servi(apps, schema_editor):
    """Migration des commandes 'recupere' vers le nouveau statut 'servi'."""
    Order = apps.get_model('core', 'Order')
    Order.objects.filter(preparation_status='recupere').update(preparation_status='servi')


def servi_to_recupere(apps, schema_editor):
    Order = apps.get_model('core', 'Order')
    Order.objects.filter(preparation_status='servi').update(preparation_status='recupere')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_seed_menu_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Renommer retrieved_at → served_at
        migrations.RenameField(
            model_name='order',
            old_name='retrieved_at',
            new_name='served_at',
        ),

        # 2. Rendre meat et side optionnels (pour les forfaits famille avec items)
        migrations.AlterField(
            model_name='order',
            name='meat',
            field=models.CharField(blank=True, max_length=100, verbose_name='Viande'),
        ),
        migrations.AlterField(
            model_name='order',
            name='side',
            field=models.CharField(blank=True, max_length=100, verbose_name='Accompagnement'),
        ),

        # 3. Mettre à jour les choix de preparation_status (recupere → servi)
        migrations.AlterField(
            model_name='order',
            name='preparation_status',
            field=models.CharField(
                choices=[
                    ('non_lance', 'Non lancé'),
                    ('en_preparation', 'En préparation'),
                    ('prepare', 'Préparé'),
                    ('servi', 'Servi'),
                ],
                default='non_lance',
                max_length=20,
                verbose_name='Préparation',
            ),
        ),

        # 4. Nouveaux champs sur Order
        migrations.AddField(
            model_name='order',
            name='change_amount',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=8, null=True,
                verbose_name='Monnaie à rendre',
                help_text='Montant de la monnaie à rendre au client.',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='supplement',
            field=models.CharField(
                blank=True, max_length=200, verbose_name='Supplément',
                help_text='Ex: viande supplémentaire, accompagnement extra...',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='supplement_price',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'), max_digits=6,
                verbose_name='Prix supplément',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_comment',
            field=models.TextField(blank=True, verbose_name='Commentaire client'),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_rating',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(10),
                ],
                verbose_name='Note client (/10)',
            ),
        ),

        # 5. Migration des données : recupere → servi
        migrations.RunPython(recupere_to_servi, servi_to_recupere),

        # 6. Créer le modèle OrderItem
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID',
                )),
                ('person_label', models.CharField(
                    blank=True,
                    help_text='Ex : Adulte 1, Enfant, Papa...',
                    max_length=100,
                    verbose_name='Personne',
                )),
                ('meat', models.CharField(blank=True, max_length=100, verbose_name='Viande')),
                ('side', models.CharField(blank=True, max_length=100, verbose_name='Accompagnement')),
                ('vegetable', models.CharField(blank=True, max_length=100, verbose_name='Légume')),
                ('supplement', models.CharField(
                    blank=True,
                    help_text='Viande ou accompagnement supplémentaire payant',
                    max_length=200,
                    verbose_name='Supplément',
                )),
                ('supplement_price', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    max_digits=6,
                    verbose_name='Prix supplément',
                )),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='core.order',
                    verbose_name='Commande',
                )),
            ],
            options={
                'verbose_name': 'Plat',
                'verbose_name_plural': 'Plats',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
