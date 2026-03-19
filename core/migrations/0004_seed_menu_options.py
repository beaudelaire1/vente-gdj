from django.db import migrations


def seed_menu_options(apps, schema_editor):
    Order = apps.get_model('core', 'Order')
    MenuOption = apps.get_model('core', 'MenuOption')

    mappings = [
        ('meat', 'meat'),
        ('side', 'side'),
        ('vegetable', 'vegetable'),
    ]

    for field_name, option_type in mappings:
        values = (
            Order.objects.exclude(**{f'{field_name}__isnull': True})
            .exclude(**{field_name: ''})
            .values_list(field_name, flat=True)
            .distinct()
        )
        for value in values:
            MenuOption.objects.get_or_create(
                option_type=option_type,
                label=value.strip(),
                defaults={'is_active': True, 'sort_order': 0},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_menuoption'),
    ]

    operations = [
        migrations.RunPython(seed_menu_options, noop),
    ]