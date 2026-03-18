import io
import qrcode
import qrcode.constants
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import Event, Order, UserProfile


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
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = get_user_role(request.user)
            if user_role not in roles and not request.user.is_superuser:
                return render(request, 'core/forbidden.html', status=403)
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        wrapper.__module__ = view_func.__module__
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

    orders = Order.objects.filter(event=event)
    stats = {
        'total': orders.count(),
        'paid': orders.filter(payment_status=Order.PAYMENT_PAYE).count(),
        'unpaid': orders.exclude(payment_status=Order.PAYMENT_PAYE).count(),
        'non_lance': orders.filter(preparation_status=Order.PREP_NON_LANCE).count(),
        'en_preparation': orders.filter(preparation_status=Order.PREP_EN_PREPARATION).count(),
        'prepare': orders.filter(preparation_status=Order.PREP_PREPARE).count(),
        'recupere': orders.filter(preparation_status=Order.PREP_RECUPERE).count(),
        'total_encaisse': orders.filter(
            payment_status=Order.PAYMENT_PAYE
        ).aggregate(s=Sum('total_amount'))['s'] or 0,
        'total_attendu': orders.aggregate(s=Sum('total_amount'))['s'] or 0,
    }

    # Répartition par viande
    meat_stats = (
        orders.values('meat')
        .annotate(count=Count('id'), total_persons=Sum('nb_persons'))
        .order_by('-count')
    )

    # Répartition par type
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
    stats = {
        'total': orders.count(),
        'paid': orders.filter(payment_status=Order.PAYMENT_PAYE).count(),
        'unpaid': orders.exclude(payment_status=Order.PAYMENT_PAYE).count(),
        'non_lance': orders.filter(preparation_status=Order.PREP_NON_LANCE).count(),
        'en_preparation': orders.filter(preparation_status=Order.PREP_EN_PREPARATION).count(),
        'prepare': orders.filter(preparation_status=Order.PREP_PREPARE).count(),
        'recupere': orders.filter(preparation_status=Order.PREP_RECUPERE).count(),
        'total_encaisse': orders.filter(
            payment_status=Order.PAYMENT_PAYE
        ).aggregate(s=Sum('total_amount'))['s'] or 0,
        'total_attendu': orders.aggregate(s=Sum('total_amount'))['s'] or 0,
    }
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
    order = get_object_or_404(Order, pk=pk)
    order.mark_paid(user=request.user)
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
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('new_status')
    try:
        order.transition_preparation(new_status, user=request.user)
    except ValueError:
        pass
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
