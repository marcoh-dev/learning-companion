from django import forms
from django.core.validators import MaxLengthValidator
from django.db.models import Q

from apps.tags.models import Tag

from .models import Profile

MAX_FOCUS_AREAS = 10


class ProfileForm(forms.ModelForm):
    new_tag = forms.CharField(max_length=30, required=False, label='New focus area')

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

    def clean_new_tag(self):
        new_tag = self.cleaned_data['new_tag'].lower()
        if ',' in new_tag:
            raise forms.ValidationError('Enter one tag at a time.')
        # Lower-casing can lengthen a string (e.g. "İ"), so check the stored form again.
        MaxLengthValidator(Tag._meta.get_field('name').max_length)(new_tag)
        return new_tag

    def clean(self):
        cleaned_data = super().clean()
        chosen = {tag.name for tag in cleaned_data.get('focus_areas', [])}
        if cleaned_data.get('new_tag'):
            chosen.add(cleaned_data['new_tag'])
        if len(chosen) > MAX_FOCUS_AREAS:
            raise forms.ValidationError(f'Choose at most {MAX_FOCUS_AREAS} focus areas.')
        return cleaned_data

    def _save_m2m(self):
        super()._save_m2m()
        new_tag = self.cleaned_data['new_tag']
        if new_tag:
            # Reuse the shared tag of that name instead of creating a duplicate.
            self.instance.focus_areas.add(Tag.objects.get_or_create(name=new_tag)[0])
