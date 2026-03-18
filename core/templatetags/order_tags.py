from django import template

register = template.Library()


@register.filter
def prep_badge_class(status):
    mapping = {
        'non_lance': 'badge-neutral',
        'en_preparation': 'badge-warning',
        'prepare': 'badge-success',
        'recupere': 'badge-muted',
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
        'recupere': '✓',
    }
    return mapping.get(status, '○')


@register.filter
def next_prep_status(status):
    mapping = {
        'non_lance': 'en_preparation',
        'en_preparation': 'prepare',
        'prepare': 'recupere',
    }
    return mapping.get(status, '')


@register.filter
def next_prep_label(status):
    mapping = {
        'non_lance': 'Lancer',
        'en_preparation': 'Marquer préparé',
        'prepare': 'Marquer récupéré',
    }
    return mapping.get(status, '')
