import uuid
from decimal import Decimal
from django.db import models, transaction
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class MenuOption(models.Model):
    TYPE_MEAT = 'meat'
    TYPE_SIDE = 'side'
    TYPE_VEGETABLE = 'vegetable'
    TYPE_CHOICES = [
        (TYPE_MEAT, 'Viande'),
        (TYPE_SIDE, 'Accompagnement'),
        (TYPE_VEGETABLE, 'Légume'),
    ]

    option_type = models.CharField("Type d'option", max_length=20, choices=TYPE_CHOICES)
    label = models.CharField("Libellé", max_length=100)
    is_active = models.BooleanField("Actif", default=True)
    sort_order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = 'Option de menu'
        verbose_name_plural = 'Options de menu'
        ordering = ['option_type', 'sort_order', 'label']
        unique_together = ['option_type', 'label']

    def __str__(self):
        return f"{self.get_option_type_display()} — {self.label}"


class Event(models.Model):
    """Campagne de vente / événement (restaurant éphémère, vente gâteaux, etc.)"""
    name = models.CharField("Nom", max_length=200)
    date = models.DateField("Date")
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Événement"
        ordering = ['-date']

    def __str__(self):
        return f"{self.name} — {self.date:%d/%m/%Y}"


class Customer(models.Model):
    """Client / inscrit"""
    name = models.CharField("Nom complet", max_length=200)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Client"
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Commande — une ligne = un plat/ticket avec son cycle de vie complet"""

    FORFAIT_INDIVIDUEL = 'individuel'
    FORFAIT_FAMILLE = 'famille'
    FORFAIT_CHOICES = [
        (FORFAIT_INDIVIDUEL, 'Individuel'),
        (FORFAIT_FAMILLE, 'Famille'),
    ]

    DINING_SUR_PLACE = 'sur_place'
    DINING_A_EMPORTER = 'a_emporter'
    DINING_CHOICES = [
        (DINING_SUR_PLACE, 'Sur place'),
        (DINING_A_EMPORTER, 'À emporter'),
    ]

    PAYMENT_NON_PAYE = 'non_paye'
    PAYMENT_PAYE = 'paye'
    PAYMENT_ATTENTE = 'attente'
    PAYMENT_CHOICES = [
        (PAYMENT_NON_PAYE, 'Non payé'),
        (PAYMENT_PAYE, 'Payé'),
        (PAYMENT_ATTENTE, 'Monnaie en attente'),
    ]

    PREP_NON_LANCE = 'non_lance'
    PREP_EN_PREPARATION = 'en_preparation'
    PREP_PREPARE = 'prepare'
    PREP_SERVI = 'servi'
    PREP_CHOICES = [
        (PREP_NON_LANCE, 'Non lancé'),
        (PREP_EN_PREPARATION, 'En préparation'),
        (PREP_PREPARE, 'Préparé'),
        (PREP_SERVI, 'Servi'),
    ]

    PREP_TRANSITIONS = {
        PREP_NON_LANCE: [PREP_EN_PREPARATION],
        PREP_EN_PREPARATION: [PREP_PREPARE],
        PREP_PREPARE: [PREP_SERVI],
        PREP_SERVI: [],
    }

    # Relations
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')

    # Identification
    ticket_number = models.PositiveIntegerField("N° Ticket")
    qr_token = models.UUIDField("Token QR", default=uuid.uuid4, unique=True, editable=False)

    # Détails commande
    forfait = models.CharField("Forfait", max_length=20, choices=FORFAIT_CHOICES)
    nb_persons = models.PositiveIntegerField("Nb personnes", default=1)
    dining_type = models.CharField("Type", max_length=20, choices=DINING_CHOICES)
    meat = models.CharField("Viande", max_length=100, blank=True)
    side = models.CharField("Accompagnement", max_length=100, blank=True)
    vegetable = models.CharField("Légume", max_length=100, blank=True)
    supplement = models.CharField(
        "Supplément", max_length=200, blank=True,
        help_text="Ex: viande supplémentaire, accompagnement extra...",
    )
    supplement_price = models.DecimalField(
        "Prix supplément", max_digits=6, decimal_places=2, default=Decimal('0.00'),
    )

    # Tarification
    unit_price = models.DecimalField("Prix unitaire", max_digits=8, decimal_places=2)
    total_amount = models.DecimalField("Montant total", max_digits=10, decimal_places=2)

    # Statuts
    payment_status = models.CharField(
        "Paiement", max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_NON_PAYE,
    )
    change_amount = models.DecimalField(
        "Monnaie à rendre", max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Montant de la monnaie à rendre au client.",
    )
    preparation_status = models.CharField(
        "Préparation", max_length=20, choices=PREP_CHOICES, default=PREP_NON_LANCE,
    )

    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField("Payé le", null=True, blank=True)
    started_at = models.DateTimeField("Lancé le", null=True, blank=True)
    prepared_at = models.DateTimeField("Préparé le", null=True, blank=True)
    served_at = models.DateTimeField("Servi le", null=True, blank=True)

    # Notes & avis
    notes = models.TextField("Notes internes", blank=True)
    customer_comment = models.TextField("Commentaire client", blank=True)
    customer_rating = models.PositiveSmallIntegerField(
        "Note client (/10)", null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )

    class Meta:
        verbose_name = "Commande"
        unique_together = ['event', 'ticket_number']
        ordering = ['ticket_number']
        indexes = [
            models.Index(fields=['event', 'preparation_status']),
            models.Index(fields=['event', 'payment_status']),
            models.Index(fields=['qr_token']),
            models.Index(fields=['ticket_number']),
            models.Index(fields=['customer_rating']),
        ]

    def __str__(self):
        return f"#{self.ticket_number} — {self.customer.name}"

    @property
    def dish_summary(self):
        # Pour les forfaits famille avec items, afficher un résumé
        if self.forfait == self.FORFAIT_FAMILLE and self.pk:
            count = self.items.count()
            if count:
                return f"{count} plat{'s' if count > 1 else ''} (famille)"
        parts = [p for p in [self.meat, self.side, self.vegetable] if p]
        if self.supplement:
            parts.append(f"+ {self.supplement}")
        return ' + '.join(parts)

    @property
    def is_paid(self):
        """Vrai si la commande est payée ou en attente de monnaie."""
        return self.payment_status in (self.PAYMENT_PAYE, self.PAYMENT_ATTENTE)

    @property
    def is_served(self):
        return self.preparation_status == self.PREP_SERVI

    def can_transition_to(self, new_status):
        return new_status in self.PREP_TRANSITIONS.get(self.preparation_status, [])

    def transition_preparation(self, new_status, user=None):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Transition impossible : {self.get_preparation_status_display()} → "
                f"{dict(self.PREP_CHOICES).get(new_status, new_status)}"
            )
        # Blocage : impossible de lancer sans paiement
        if new_status == self.PREP_EN_PREPARATION and self.payment_status == self.PAYMENT_NON_PAYE:
            raise ValueError(
                "Impossible de lancer la préparation : la commande n'est pas encore payée."
            )
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if new_status == self.PREP_EN_PREPARATION and order.payment_status == self.PAYMENT_NON_PAYE:
                raise ValueError(
                    "Impossible de lancer la préparation : la commande n'est pas encore payée."
                )
            if not order.can_transition_to(new_status):
                raise ValueError("Transition déjà effectuée par un autre utilisateur.")
            old_status = order.preparation_status
            order.preparation_status = new_status
            now = timezone.now()
            if new_status == self.PREP_EN_PREPARATION:
                order.started_at = now
            elif new_status == self.PREP_PREPARE:
                order.prepared_at = now
            elif new_status == self.PREP_SERVI:
                order.served_at = now
            order.save()
            StatusLog.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                changed_by=user,
            )
            # Refresh self from DB
            self.preparation_status = order.preparation_status
            self.started_at = order.started_at
            self.prepared_at = order.prepared_at
            self.served_at = order.served_at
            self.updated_at = order.updated_at

    def mark_paid(self, user=None):
        if self.payment_status == self.PAYMENT_PAYE:
            return
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.payment_status == self.PAYMENT_PAYE:
                return
            old = order.payment_status
            order.payment_status = self.PAYMENT_PAYE
            order.change_amount = None
            order.paid_at = timezone.now()
            order.save()
            StatusLog.objects.create(
                order=order, old_status=f'pay:{old}',
                new_status=f'pay:{self.PAYMENT_PAYE}', changed_by=user,
            )
            # Refresh self
            self.payment_status = order.payment_status
            self.change_amount = None
            self.paid_at = order.paid_at

    def mark_payment_pending(self, change_amount, user=None):
        """Marque la commande comme payée avec monnaie en attente."""
        if self.payment_status == self.PAYMENT_PAYE:
            return
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=self.pk)
            if order.payment_status == self.PAYMENT_PAYE:
                return
            old = order.payment_status
            order.payment_status = self.PAYMENT_ATTENTE
            order.change_amount = change_amount
            order.paid_at = timezone.now()
            order.save()
            StatusLog.objects.create(
                order=order, old_status=f'pay:{old}',
                new_status=f'pay:{self.PAYMENT_ATTENTE}', changed_by=user,
            )
            # Refresh self
            self.payment_status = order.payment_status
            self.change_amount = order.change_amount
            self.paid_at = order.paid_at

    def submit_review(self, rating, comment=''):
        """Enregistre l'avis client (note sur 10 + commentaire optionnel)."""
        if self.customer_rating is not None:
            return  # Avis déjà soumis
        Order.objects.filter(pk=self.pk).update(
            customer_rating=rating,
            customer_comment=comment,
        )
        self.customer_rating = rating
        self.customer_comment = comment

    def compute_total(self):
        """Calcule le tarif selon les règles métier."""
        price = Decimal('20.00') if self.dining_type == self.DINING_SUR_PLACE else Decimal('15.00')
        self.unit_price = price
        total = price * self.nb_persons
        if self.forfait == self.FORFAIT_FAMILLE and self.nb_persons >= 5:
            total = total * Decimal('0.85')
        # Supplément au niveau de la commande
        total += (self.supplement_price or Decimal('0.00'))
        # Suppléments des plats individuels (si déjà sauvegardé)
        if self.pk:
            items_extra = self.items.aggregate(s=Sum('supplement_price'))['s'] or Decimal('0.00')
            total += items_extra
        self.total_amount = total.quantize(Decimal('0.01'))


class StatusLog(models.Model):
    """Historique des changements de statut"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique statut"
        ordering = ['-changed_at']

    def __str__(self):
        return f"#{self.order.ticket_number} {self.old_status} → {self.new_status}"


class UserProfile(models.Model):
    """Extension du profil utilisateur pour les rôles"""
    ROLE_ADMIN = 'admin'
    ROLE_CAISSE = 'caisse'
    ROLE_PREPARATION = 'preparation'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrateur'),
        (ROLE_CAISSE, 'Caisse'),
        (ROLE_PREPARATION, 'Préparation / Distribution'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile',
    )
    role = models.CharField("Rôle", max_length=20, choices=ROLE_CHOICES, default=ROLE_CAISSE)

    class Meta:
        verbose_name = "Profil utilisateur"

    def __str__(self):
        return f"{self.user.username} — {self.get_role_display()}"


class Notification(models.Model):
    """Notification envoyée à chaque changement d'état via signals."""
    TYPE_PREP = 'preparation'
    TYPE_PAYMENT = 'payment'
    TYPE_CHOICES = [
        (TYPE_PREP, 'Préparation'),
        (TYPE_PAYMENT, 'Paiement'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    target_role = models.CharField(max_length=20, choices=UserProfile.ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_role', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} — #{self.order.ticket_number}"


class OrderItem(models.Model):
    """Détail d'un plat individuel au sein d'une commande (forfait famille)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande",
    )
    person_label = models.CharField(
        "Personne", max_length=100, blank=True,
        help_text="Ex : Adulte 1, Enfant, Papa...",
    )
    meat = models.CharField("Viande", max_length=100, blank=True)
    side = models.CharField("Accompagnement", max_length=100, blank=True)
    vegetable = models.CharField("Légume", max_length=100, blank=True)
    supplement = models.CharField(
        "Supplément", max_length=200, blank=True,
        help_text="Viande ou accompagnement supplémentaire payant",
    )
    supplement_price = models.DecimalField(
        "Prix supplément", max_digits=6, decimal_places=2, default=Decimal('0.00'),
    )
    sort_order = models.PositiveSmallIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Plat"
        verbose_name_plural = "Plats"
        ordering = ['sort_order', 'id']

    def __str__(self):
        parts = [p for p in [self.meat, self.side, self.vegetable] if p]
        label = ' + '.join(parts) or "Plat vide"
        if self.person_label:
            return f"{self.person_label} : {label}"
        return label

    @property
    def dish_summary(self):
        parts = [p for p in [self.meat, self.side, self.vegetable] if p]
        if self.supplement:
            parts.append(f"+ {self.supplement}")
        return ' + '.join(parts)
