from django.contrib import admin
from .models import Event, Customer, Order, StatusLog, UserProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number', 'customer', 'event', 'meat', 'side',
        'dining_type', 'total_amount', 'payment_status', 'preparation_status',
    )
    list_filter = ('event', 'payment_status', 'preparation_status', 'dining_type', 'forfait')
    search_fields = ('customer__name', 'ticket_number')
    readonly_fields = ('qr_token', 'created_at', 'updated_at')


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
