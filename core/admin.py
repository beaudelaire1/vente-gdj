from django.contrib import admin
from .forms import OrderAdminForm
from .models import Event, Customer, Order, StatusLog, UserProfile, Notification, MenuOption


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_active', 'created_at')
    list_filter = ('is_active',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone')


@admin.register(MenuOption)
class MenuOptionAdmin(admin.ModelAdmin):
    list_display = ('label', 'option_type', 'sort_order', 'is_active')
    list_filter = ('option_type', 'is_active')
    search_fields = ('label',)
    ordering = ('option_type', 'sort_order', 'label')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = (
        'ticket_number', 'customer', 'event', 'meat', 'side',
        'dining_type', 'total_amount', 'payment_status', 'preparation_status',
    )
    list_filter = ('event', 'payment_status', 'preparation_status', 'dining_type', 'forfait')
    search_fields = ('customer__name', 'ticket_number')
    readonly_fields = ('qr_token', 'created_at', 'updated_at', 'paid_at', 'started_at', 'prepared_at', 'retrieved_at')


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status',)
    readonly_fields = ('order', 'old_status', 'new_status', 'changed_by', 'changed_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'notification_type', 'target_role', 'is_read', 'created_at')
    list_filter = ('notification_type', 'target_role', 'is_read')
    readonly_fields = ('order', 'notification_type', 'title', 'message', 'target_role', 'created_at')
