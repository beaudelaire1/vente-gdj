import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


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
    PREP_RECUPERE = 'recupere'
    PREP_CHOICES = [
        (PREP_NON_LANCE, 'Non lancé'),
        (PREP_EN_PREPARATION, 'En préparation'),
        (PREP_PREPARE, 'Préparé'),
        (PREP_RECUPERE, 'Récupéré'),
    ]

    PREP_TRANSITIONS = {
        PREP_NON_LANCE: [PREP_EN_PREPARATION],
        PREP_EN_PREPARATION: [PREP_PREPARE],
        PREP_PREPARE: [PREP_RECUPERE],
        PREP_RECUPERE: [],
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
    meat = models.CharField("Viande", max_length=100)
    side = models.CharField("Accompagnement", max_length=100)
    vegetable = models.CharField("Légume", max_length=100, blank=True)

    # Tarification
    unit_price = models.DecimalField("Prix unitaire", max_digits=8, decimal_places=2)
    total_amount = models.DecimalField("Montant total", max_digits=10, decimal_places=2)

    # Statuts
    payment_status = models.CharField(
        "Paiement", max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_NON_PAYE,
    )
    preparation_status = models.CharField(
        "Préparation", max_length=20, choices=PREP_CHOICES, default=PREP_NON_LANCE,
    )

    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField("Payé le", null=True, blank=True)
    prepared_at = models.DateTimeField("Préparé le", null=True, blank=True)
    retrieved_at = models.DateTimeField("Récupéré le", null=True, blank=True)

    # Notes
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Commande"
        unique_together = ['event', 'ticket_number']
        ordering = ['ticket_number']

    def __str__(self):
        return f"#{self.ticket_number} — {self.customer.name}"

    @property
    def dish_summary(self):
        parts = [self.meat, self.side]
        if self.vegetable:
            parts.append(self.vegetable)
        return ' + '.join(parts)

    @property
    def is_paid(self):
        return self.payment_status == self.PAYMENT_PAYE

    @property
    def is_retrieved(self):
        return self.preparation_status == self.PREP_RECUPERE

    def can_transition_to(self, new_status):
        return new_status in self.PREP_TRANSITIONS.get(self.preparation_status, [])

    def transition_preparation(self, new_status, user=None):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Transition impossible : {self.get_preparation_status_display()} → "
                f"{dict(self.PREP_CHOICES).get(new_status, new_status)}"
            )
        old_status = self.preparation_status
        self.preparation_status = new_status
        now = timezone.now()
        if new_status == self.PREP_PREPARE:
            self.prepared_at = now
        elif new_status == self.PREP_RECUPERE:
            self.retrieved_at = now
        self.save()
        StatusLog.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
        )

    def mark_paid(self, user=None):
        if self.payment_status == self.PAYMENT_PAYE:
            return
        old = self.payment_status
        self.payment_status = self.PAYMENT_PAYE
        self.paid_at = timezone.now()
        self.save()
        StatusLog.objects.create(
            order=self, old_status=f'pay:{old}',
            new_status=f'pay:{self.PAYMENT_PAYE}', changed_by=user,
        )

    def compute_total(self):
        """Calcule le tarif selon les règles métier."""
        price = Decimal('20.00') if self.dining_type == self.DINING_SUR_PLACE else Decimal('15.00')
        self.unit_price = price
        total = price * self.nb_persons
        if self.forfait == self.FORFAIT_FAMILLE and self.nb_persons >= 5:
            total = total * Decimal('0.85')
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
