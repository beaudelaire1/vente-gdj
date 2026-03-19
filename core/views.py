import io
import csv
import qrcode
import qrcode.constants
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Event, Order, UserProfile, Notification

from functools import wraps


# ── Helpers ──────────────────────────────────────────────────────────

def get_active_event():
    return Event.objects.filter(is_active=True).first()


def get_user_role(user):
    if user.is_superuser:
        return UserProfile.ROLE_ADMIN
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return UserProfile.ROLE_CAISSE


def role_required(*roles):
    """Décorateur pour restreindre l'accès par rôle."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = get_user_role(request.user)
            if user_role not in roles and not request.user.is_superuser:
                return render(request, 'core/forbidden.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── Authentification ──────────────────────────────────────────────────

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            role = get_user_role(user)
            if role == UserProfile.ROLE_PREPARATION:
                return redirect('preparation')
            elif role == UserProfile.ROLE_CAISSE:
                return redirect('caisse')
            return redirect('dashboard')
        error = "Identifiants incorrects."
    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Dashboard ──────────────────────────────────────────────────────────

@login_required
@role_required(UserProfile.ROLE_ADMIN)
def dashboard_view(request):
    event = get_active_event()
    if not event:
        return render(request, 'core/dashboard.html', {'event': None})

    orders = Order.objects.filter(event=event).select_related('customer')
    stats = orders.aggregate(
        total=Count('id'),
        paid=Count('id', filter=Q(payment_status=Order.PAYMENT_PAYE)),
        unpaid=Count('id', filter=~Q(payment_status=Order.PAYMENT_PAYE)),
        non_lance=Count('id', filter=Q(preparation_status=Order.PREP_NON_LANCE)),
        en_preparation=Count('id', filter=Q(preparation_status=Order.PREP_EN_PREPARATION)),
        prepare=Count('id', filter=Q(preparation_status=Order.PREP_PREPARE)),
        recupere=Count('id', filter=Q(preparation_status=Order.PREP_RECUPERE)),
        total_encaisse=Sum('total_amount', filter=Q(payment_status=Order.PAYMENT_PAYE)),
        total_attendu=Sum('total_amount'),
    )
    stats['total_encaisse'] = stats['total_encaisse'] or 0
    stats['total_attendu'] = stats['total_attendu'] or 0

    # Temps moyen de préparation
    prep_times = orders.filter(
        started_at__isnull=False, prepared_at__isnull=False
    ).annotate(
        prep_duration=F('prepared_at') - F('started_at')
    ).aggregate(avg_prep=Avg('prep_duration'))
    stats['avg_prep_minutes'] = (
        round(prep_times['avg_prep'].total_seconds() / 60, 1)
        if prep_times['avg_prep'] else None
    )

    # Répartitions
    meat_stats = (
        orders.values('meat')
        .annotate(count=Count('id'), total_persons=Sum('nb_persons'))
        .order_by('-count')
    )
    dining_stats = (
        orders.values('dining_type')
        .annotate(count=Count('id'))
        .order_by('dining_type')
    )

    return render(request, 'core/dashboard.html', {
        'event': event,
        'stats': stats,
        'meat_stats': meat_stats,
        'dining_stats': dining_stats,
        'orders': orders,
    })


@login_required
@role_required(UserProfile.ROLE_ADMIN)
def dashboard_stats_partial(request):
    """Fragment HTMX pour rafraîchir les stats."""
    event = get_active_event()
    if not event:
        return HttpResponse('')
    orders = Order.objects.filter(event=event)
    stats = orders.aggregate(
        total=Count('id'),
        paid=Count('id', filter=Q(payment_status=Order.PAYMENT_PAYE)),
        unpaid=Count('id', filter=~Q(payment_status=Order.PAYMENT_PAYE)),
        non_lance=Count('id', filter=Q(preparation_status=Order.PREP_NON_LANCE)),
        en_preparation=Count('id', filter=Q(preparation_status=Order.PREP_EN_PREPARATION)),
        prepare=Count('id', filter=Q(preparation_status=Order.PREP_PREPARE)),
        recupere=Count('id', filter=Q(preparation_status=Order.PREP_RECUPERE)),
        total_encaisse=Sum('total_amount', filter=Q(payment_status=Order.PAYMENT_PAYE)),
        total_attendu=Sum('total_amount'),
    )
    stats['total_encaisse'] = stats['total_encaisse'] or 0
    stats['total_attendu'] = stats['total_attendu'] or 0

    prep_times = orders.filter(
        started_at__isnull=False, prepared_at__isnull=False
    ).annotate(
        prep_duration=F('prepared_at') - F('started_at')
    ).aggregate(avg_prep=Avg('prep_duration'))
    stats['avg_prep_minutes'] = (
        round(prep_times['avg_prep'].total_seconds() / 60, 1)
        if prep_times['avg_prep'] else None
    )

    return render(request, 'core/partials/dashboard_stats.html', {'stats': stats, 'event': event})


# ── Caisse ─────────────────────────────────────────────────────────────

@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_CAISSE)
def caisse_view(request):
    event = get_active_event()
    if not event:
        return render(request, 'core/caisse.html', {'event': None})
    return render(request, 'core/caisse.html', {'event': event})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_CAISSE)
def caisse_search(request):
    """Recherche HTMX pour la caisse."""
    event = get_active_event()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    orders = Order.objects.filter(event=event).select_related('customer')

    if q:
        filters = Q(customer__name__icontains=q) | Q(customer__phone__icontains=q)
        if q.isdigit():
            filters |= Q(ticket_number=int(q))
        orders = orders.filter(filters)

    if status_filter:
        if status_filter == 'paye':
            orders = orders.filter(payment_status=Order.PAYMENT_PAYE)
        elif status_filter == 'non_paye':
            orders = orders.exclude(payment_status=Order.PAYMENT_PAYE)

    return render(request, 'core/partials/caisse_results.html', {'orders': orders[:50]})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_CAISSE)
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer', 'event'), pk=pk)
    return render(request, 'core/order_detail.html', {'order': order})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_CAISSE)
def order_detail_partial(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer', 'event'), pk=pk)
    return render(request, 'core/partials/order_card.html', {'order': order})


@require_POST
@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_CAISSE)
def mark_paid(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer'), pk=pk)
    order.mark_paid(user=request.user)
    messages.success(request, f'Commande #{order.ticket_number} marquée comme payée.')
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/order_card.html', {'order': order})
    return redirect('order_detail', pk=pk)


# ── Préparation / Distribution ──────────────────────────────────────

@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_PREPARATION)
def preparation_view(request):
    event = get_active_event()
    if not event:
        return render(request, 'core/preparation.html', {'event': None})
    return render(request, 'core/preparation.html', {'event': event})


@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_PREPARATION)
def preparation_list(request):
    """Fragment HTMX — liste filtrée des commandes pour la préparation."""
    event = get_active_event()
    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()

    orders = Order.objects.filter(event=event).select_related('customer')

    if status_filter:
        orders = orders.filter(preparation_status=status_filter)

    if q:
        filters = Q(customer__name__icontains=q)
        if q.isdigit():
            filters |= Q(ticket_number=int(q))
        orders = orders.filter(filters)

    return render(request, 'core/partials/preparation_list.html', {'orders': orders[:100]})


@require_POST
@login_required
@role_required(UserProfile.ROLE_ADMIN, UserProfile.ROLE_PREPARATION)
def transition_status(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer'), pk=pk)
    new_status = request.POST.get('new_status')
    valid_statuses = dict(Order.PREP_CHOICES)
    if new_status not in valid_statuses:
        messages.error(request, "Statut invalide.")
        if request.headers.get('HX-Request'):
            return render(request, 'core/partials/prep_card.html', {'order': order})
        return redirect('preparation')
    try:
        order.transition_preparation(new_status, user=request.user)
        messages.success(request, f'#{order.ticket_number} → {valid_statuses[new_status]}')
    except ValueError as e:
        messages.error(request, str(e))
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/prep_card.html', {'order': order})
    return redirect('preparation')


# ── QR Code / Consultation publique ──────────────────────────────────

def order_public_view(request, token):
    """Page de consultation publique accessible via QR code."""
    order = get_object_or_404(
        Order.objects.select_related('customer', 'event'), qr_token=token,
    )
    return render(request, 'core/public_order.html', {'order': order})


def order_public_status(request, token):
    """Fragment HTMX pour auto-refresh du statut."""
    order = get_object_or_404(Order, qr_token=token)
    return render(request, 'core/partials/public_status.html', {'order': order})


def qr_code_image(request, token):
    """Génère l'image QR code pour un token donné."""
    order = get_object_or_404(Order, qr_token=token)
    base_url = request.build_absolute_uri(f'/suivi/{order.qr_token}/')
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(base_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


# ── Ticket impression ────────────────────────────────────────────────

@login_required
def ticket_print_view(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer', 'event'), pk=pk)
    return render(request, 'core/ticket_print.html', {'order': order})


# ── Notifications ────────────────────────────────────────────────────

@login_required
def notifications_partial(request):
    """Fragment HTMX — notifications non lues pour le rôle de l'utilisateur."""
    role = get_user_role(request.user)
    notifs = Notification.objects.filter(
        target_role=role, is_read=False
    ).select_related('order')[:20]
    return render(request, 'core/partials/notifications.html', {
        'notifications': notifs,
        'notif_count': notifs.count(),
    })


@login_required
def notifications_count(request):
    """HTML snippet pour le badge de count (HTMX)."""
    role = get_user_role(request.user)
    count = Notification.objects.filter(target_role=role, is_read=False).count()
    if count > 0:
        return HttpResponse(f'<span class="notif-badge">{count}</span>')
    return HttpResponse('')


@require_POST
@login_required
def notifications_mark_read(request):
    """Marquer toutes les notifications comme lues."""
    role = get_user_role(request.user)
    Notification.objects.filter(target_role=role, is_read=False).update(is_read=True)
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/notifications.html', {
            'notifications': [],
            'notif_count': 0,
        })
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ── Export CSV ───────────────────────────────────────────────────────

@login_required
@role_required(UserProfile.ROLE_ADMIN)
def export_csv(request):
    """Export des commandes de l'événement actif en CSV."""
    event = get_active_event()
    if not event:
        messages.error(request, "Aucun événement actif.")
        return redirect('dashboard')

    orders = Order.objects.filter(event=event).select_related('customer').order_by('ticket_number')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="commandes_{event.date}.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'N° Ticket', 'Client', 'Téléphone', 'Forfait', 'Personnes',
        'Type', 'Viande', 'Accompagnement', 'Légume',
        'Prix unitaire', 'Total', 'Paiement', 'Préparation',
        'Créé le', 'Payé le', 'Préparé le', 'Récupéré le',
    ])
    for o in orders:
        writer.writerow([
            o.ticket_number, o.customer.name, o.customer.phone,
            o.get_forfait_display(), o.nb_persons,
            o.get_dining_type_display(), o.meat, o.side, o.vegetable,
            o.unit_price, o.total_amount,
            o.get_payment_status_display(), o.get_preparation_status_display(),
            o.created_at.strftime('%d/%m/%Y %H:%M') if o.created_at else '',
            o.paid_at.strftime('%d/%m/%Y %H:%M') if o.paid_at else '',
            o.prepared_at.strftime('%d/%m/%Y %H:%M') if o.prepared_at else '',
            o.retrieved_at.strftime('%d/%m/%Y %H:%M') if o.retrieved_at else '',
        ])
    return response
