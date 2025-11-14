import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RenewBookForm(forms.Form):
    """
    Форма обновления книг для библиотекарей
    """
    renewal_date = forms.DateField(
        help_text="Enter a date between now and 4 weeks (default 3).",
        widget=forms.DateInput(attrs={'type': 'date'})  # Добавьте это для HTML5 date picker
    )

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Проверка, что дата не в прошлом
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Проверка, что дата не в "далёком" будущем (+4 недели)
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Всегда надо возвращать очищенные данные
        return data