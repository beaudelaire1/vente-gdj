from django import forms

from .models import MenuOption, Order, OrderItem


def _menu_choices(option_type, allow_blank=True, current_value=''):
    """Build choices list from MenuOption for a given type."""
    options = list(
        MenuOption.objects.filter(option_type=option_type, is_active=True)
        .order_by('sort_order', 'label')
        .values_list('label', flat=True)
    )
    if current_value and current_value not in options:
        options.append(current_value)
    choices = [(v, v) for v in options]
    if allow_blank:
        choices = [('', '---------')] + choices
    return choices


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pour les forfaits famille, meat/side peuvent être vides (gérés via les plats individuels)
        self._configure_menu_field('meat', MenuOption.TYPE_MEAT, allow_blank=True)
        self._configure_menu_field('side', MenuOption.TYPE_SIDE, allow_blank=True)
        self._configure_menu_field('vegetable', MenuOption.TYPE_VEGETABLE, allow_blank=True)

    def _configure_menu_field(self, field_name, option_type, allow_blank=False):
        current_value = self.initial.get(field_name) or getattr(self.instance, field_name, '')
        choices = _menu_choices(option_type, allow_blank=allow_blank, current_value=current_value)
        self.fields[field_name] = forms.ChoiceField(
            choices=choices,
            required=not allow_blank,
            label=self.fields[field_name].label,
            help_text=self.fields[field_name].help_text,
        )

    def clean(self):
        cleaned_data = super().clean()
        forfait = cleaned_data.get('forfait')
        meat = cleaned_data.get('meat', '')
        side = cleaned_data.get('side', '')
        # Pour un forfait individuel, viande et accompagnement sont obligatoires
        # (sauf si on utilise les plats individuels — cas famille géré via inline)
        if forfait == Order.FORFAIT_INDIVIDUEL:
            if not meat:
                self.add_error('meat', "La viande est obligatoire pour un forfait individuel.")
            if not side:
                self.add_error('side', "L'accompagnement est obligatoire pour un forfait individuel.")
        return cleaned_data


class OrderItemAdminForm(forms.ModelForm):
    """Formulaire inline OrderItem avec listes déroulantes pour viande/accomp/légume."""

    class Meta:
        model = OrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, option_type in [
            ('meat', MenuOption.TYPE_MEAT),
            ('side', MenuOption.TYPE_SIDE),
            ('vegetable', MenuOption.TYPE_VEGETABLE),
        ]:
            current_value = self.initial.get(field_name) or getattr(self.instance, field_name, '')
            choices = _menu_choices(option_type, allow_blank=True, current_value=current_value)
            self.fields[field_name] = forms.ChoiceField(
                choices=choices,
                required=False,
                label=self.fields[field_name].label,
            )
