from django import forms

from .models import MenuOption, Order


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_menu_field('meat', MenuOption.TYPE_MEAT)
        self._configure_menu_field('side', MenuOption.TYPE_SIDE)
        self._configure_menu_field('vegetable', MenuOption.TYPE_VEGETABLE, allow_blank=True)

    def _configure_menu_field(self, field_name, option_type, allow_blank=False):
        current_value = self.initial.get(field_name) or getattr(self.instance, field_name, '')
        options = list(
            MenuOption.objects.filter(option_type=option_type, is_active=True)
            .order_by('sort_order', 'label')
            .values_list('label', flat=True)
        )

        if current_value and current_value not in options:
            options.append(current_value)

        choices = [(value, value) for value in options]
        if allow_blank:
            choices = [('', '---------')] + choices

        self.fields[field_name] = forms.ChoiceField(
            choices=choices,
            required=not allow_blank,
            label=self.fields[field_name].label,
            help_text=self.fields[field_name].help_text,
        )
