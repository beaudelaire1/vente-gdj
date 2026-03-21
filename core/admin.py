from django.contrib import admin
from .forms import OrderAdminForm, OrderItemAdminForm
from .models import Event, Customer, Order, OrderItem, StatusLog, UserProfile, Notification, MenuOption


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


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemAdminForm
    extra = 1
    fields = ('sort_order', 'person_label', 'meat', 'side', 'vegetable', 'supplement', 'supplement_price')
    verbose_name = "Plat"
    verbose_name_plural = "Détail des plats (forfait famille)"

    def get_extra(self, request, obj=None, **kwargs):
        # Pour les nouvelles commandes famille, afficher 2 lignes par défaut
        if obj and obj.forfait == Order.FORFAIT_FAMILLE:
            return max(0, (obj.nb_persons or 1) - obj.items.count())
        return 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    inlines = [OrderItemInline]
    list_display = (
        'ticket_number', 'customer', 'event', 'forfait', 'nb_persons',
        'dining_type', 'total_amount', 'payment_status', 'preparation_status',
        'customer_rating',
    )
    list_filter = ('event', 'payment_status', 'preparation_status', 'dining_type', 'forfait')
    search_fields = ('customer__name', 'ticket_number')
    readonly_fields = (
        'qr_token', 'created_at', 'updated_at', 'paid_at',
        'started_at', 'prepared_at', 'served_at',
    )
    fieldsets = (
        ('Identification', {
            'fields': ('event', 'customer', 'ticket_number', 'qr_token'),
        }),
        ('Commande', {
            'fields': ('forfait', 'nb_persons', 'dining_type', 'meat', 'side', 'vegetable',
                       'supplement', 'supplement_price'),
        }),
        ('Tarification', {
            'fields': ('unit_price', 'total_amount'),
        }),
        ('Paiement', {
            'fields': ('payment_status', 'change_amount', 'paid_at'),
        }),
        ('Préparation', {
            'fields': ('preparation_status', 'started_at', 'prepared_at', 'served_at'),
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
        ('Avis client', {
            'fields': ('customer_rating', 'customer_comment'),
            'classes': ('collapse',),
        }),
        ('Horodatage', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_formset(self, request, form, formset, change):
        """Synchronise nb_persons depuis les items après sauvegarde des inlines."""
        super().save_formset(request, form, formset, change)
        if formset.model == OrderItem:
            order = form.instance
            if order.forfait == Order.FORFAIT_FAMILLE:
                count = order.items.count()
                if count > 0 and count != order.nb_persons:
                    Order.objects.filter(pk=order.pk).update(nb_persons=count)


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
