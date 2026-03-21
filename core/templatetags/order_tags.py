from django import template
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def prep_badge_class(status):
    mapping = {
        'non_lance': 'badge-status-idle',
        'en_preparation': 'badge-status-progress',
        'prepare': 'badge-status-ready',
        'servi': 'badge-status-done',
    }
    return mapping.get(status, 'badge-neutral')


@register.filter
def payment_badge_class(status):
    mapping = {
        'non_paye': 'badge-danger',
        'paye': 'badge-success',
        'attente': 'badge-warning',
    }
    return mapping.get(status, 'badge-neutral')


@register.filter
def prep_icon(status):
    mapping = {
        'non_lance': '○',
        'en_preparation': '◔',
        'prepare': '●',
        'servi': '✓',
    }
    return mapping.get(status, '○')


@register.filter
def next_prep_status(status):
    mapping = {
        'non_lance': 'en_preparation',
        'en_preparation': 'prepare',
        'prepare': 'servi',
    }
    return mapping.get(status, '')


@register.filter
def next_prep_label(status):
    mapping = {
        'non_lance': '🚀 Lancer la préparation',
        'en_preparation': '✅ Marquer préparé',
        'prepare': '🍽 Marquer servi',
    }
    return mapping.get(status, '')


@register.filter
def next_prep_btn_class(status):
    """Classe CSS du bouton de transition selon le statut actuel."""
    mapping = {
        'non_lance': 'btn-primary',
        'en_preparation': 'btn-success',
        'prepare': 'btn-ghost',
    }
    return mapping.get(status, 'btn-primary')


@register.filter
def prep_row_class(status):
    """Classe CSS pour colorer les lignes du tableau caisse par statut."""
    return f'row-status-{status}'


@register.filter
def time_ago(value):
    """Affiche le temps écoulé depuis une date."""
    if not value:
        return ''
    return timesince(value)
