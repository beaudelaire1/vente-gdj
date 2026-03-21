from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/stats/', views.dashboard_stats_partial, name='dashboard_stats'),

    # Caisse
    path('caisse/', views.caisse_view, name='caisse'),
    path('caisse/search/', views.caisse_search, name='caisse_search'),
    path('commande/<int:pk>/', views.order_detail, name='order_detail'),
    path('commande/<int:pk>/partial/', views.order_detail_partial, name='order_detail_partial'),
    path('commande/<int:pk>/payer/', views.mark_paid, name='mark_paid'),
    path('commande/<int:pk>/monnaie/', views.mark_payment_pending, name='mark_payment_pending'),
    path('commande/<int:pk>/ticket/', views.ticket_print_view, name='ticket_print'),

    # Préparation
    path('preparation/', views.preparation_view, name='preparation'),
    path('preparation/list/', views.preparation_list, name='preparation_list'),
    path('commande/<int:pk>/transition/', views.transition_status, name='transition_status'),

    # Notifications
    path('notifications/', views.notifications_partial, name='notifications_partial'),
    path('notifications/count/', views.notifications_count, name='notifications_count'),
    path('notifications/read/', views.notifications_mark_read, name='notifications_mark_read'),

    # Export
    path('export/csv/', views.export_csv, name='export_csv'),

    # Public / QR
    path('suivi/<uuid:token>/', views.order_public_view, name='order_public'),
    path('suivi/<uuid:token>/status/', views.order_public_status, name='order_public_status'),
    path('suivi/<uuid:token>/avis/', views.submit_review, name='submit_review'),
    path('qr/<uuid:token>.png', views.qr_code_image, name='qr_code_image'),
]
