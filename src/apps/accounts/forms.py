from django import forms
from django.db.models import Q

from apps.tags.models import Tag

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'cohort', 'focus_areas']
        widgets = {'focus_areas': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Offer the curated starter tags plus this profile's own tags, never other users' tags.
        self.fields['focus_areas'].queryset = Tag.objects.filter(
            Q(starter=True) | Q(profiles=self.instance)
        ).distinct()
