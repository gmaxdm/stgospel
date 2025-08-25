#coding=utf-8
from django.utils.translation import gettext_lazy as _
from django import forms

from bible.models import BOOKS


class GroupCreateForm(forms.Form):
    name = forms.CharField()
    volume = forms.IntegerField(required=False)
    book_id = forms.MultipleChoiceField(required=False,
                                        choices=((b, b) for b in range(1, BOOKS+1)))
    chpd = forms.IntegerField(min_value=1, max_value=10, required=False)
    start_idx = forms.IntegerField(min_value=1, required=False)
    names_cnt = forms.IntegerField(min_value=0, max_value=10, required=False)
    start = forms.DateField(required=False)
    end = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data["volume"] == -1 and len(cleaned_data["book_id"]) == 0:
            raise forms.ValidationError("Выберите, пожалуйста, сборник или "
                                        "одну или несколько книг")

