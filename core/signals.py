from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, StatusLog, Notification, UserProfile


@receiver(post_save, sender=StatusLog)
def create_notification_on_status_change(sender, instance, created, **kwargs):
    """Crée une notification à chaque changement d'état (préparation ou paiement)."""
    if not created:
        return

    log = instance
    order = log.order

    if log.new_status.startswith('pay:'):
        # Notification paiement → pour la préparation
        status_label = log.new_status.replace('pay:', '')
        if status_label == 'paye':
            Notification.objects.create(
                order=order,
                notification_type=Notification.TYPE_PAYMENT,
                title=f'Paiement confirmé #{order.ticket_number}',
                message=f'La commande #{order.ticket_number} de {order.customer.name} a été payée ({order.total_amount}€).',
                target_role=UserProfile.ROLE_PREPARATION,
            )

            # Lancer automatiquement la préparation si elle n'a pas encore démarré
            order.refresh_from_db(fields=['preparation_status'])
            if order.preparation_status == Order.PREP_NON_LANCE:
                order.transition_preparation(Order.PREP_EN_PREPARATION, user=log.changed_by)
    else:
        # Notification préparation → pour la caisse et l'admin
        labels = dict(order.PREP_CHOICES)
        new_label = labels.get(log.new_status, log.new_status)

        Notification.objects.create(
            order=order,
            notification_type=Notification.TYPE_PREP,
            title=f'#{order.ticket_number} → {new_label}',
            message=f'La commande #{order.ticket_number} ({order.customer.name}) est passée à « {new_label} ».',
            target_role=UserProfile.ROLE_CAISSE,
        )

        # Aussi notifier l'admin
        Notification.objects.create(
            order=order,
            notification_type=Notification.TYPE_PREP,
            title=f'#{order.ticket_number} → {new_label}',
            message=f'La commande #{order.ticket_number} ({order.customer.name}) est passée à « {new_label} ».',
            target_role=UserProfile.ROLE_ADMIN,
        )
