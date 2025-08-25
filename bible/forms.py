from django import forms

from .models import Volume


class VolumeCreateForm(forms.ModelForm):
    title = forms.CharField()

    class Meta:
        model = Volume
        fields = ("title",)

