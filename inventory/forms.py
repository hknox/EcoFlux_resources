from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Layout, Row, Column, Field, Submit, HTML
from crispy_forms.bootstrap import AppendedText
from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import (
    Site,
    DOI,
    Photo,
    FieldNote,
)


class FieldNoteForm(forms.ModelForm):
    class Meta:
        model = FieldNote
        fields = ["note", "user"]


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["image", "caption"]


class DOIForm(forms.ModelForm):
    class Meta:
        model = DOI
        fields = ["label", "doi_link"]
        labels = {
            "doi_link": "DOI link",
        }


DOIFormSet = inlineformset_factory(Site, DOI, form=DOIForm, extra=1, can_delete=True)
FieldnoteFormSet = inlineformset_factory(
    Site, FieldNote, form=FieldNoteForm, extra=1, can_delete=True
)
PhotoFormSet = inlineformset_factory(
    Site, Photo, form=PhotoForm, extra=1, can_delete=True
)


class DOIFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.layout = Layout(
            Row(
                Column(FloatingField("label"), css_class="col-md-5"),
                Column(FloatingField("doi_link"), css_class="col-md-5"),
                Column(Field("DELETE"), css_class="col-md-2"),
                css_class="mb-2",
            )
        )


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            "name",
            "code",
            "amp",
            "location",
            "description",
            "date_activated",
            "date_retired",
            "gps_coordinates",
        ]
        widgets = {
            "date_activated": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",
                    "placeholder": "YYYY-MM-DD",
                }
            ),
            "date_retired": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",
                    "placeholder": "YYYY-MM-DD",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "style": "min-height: 120px;",  # extra space
                }
            ),
            "location": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "style": "min-height: 90px;",  # extra space
                }
            ),
        }

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False

        # helper.form_id = 'some-id'
        helper.form_method = "post"
        helper.form_action = "sites"
        helper.layout = Layout(
            Row(
                Column(
                    FloatingField("name", css_class="col-md-6"),
                ),
                Column(
                    FloatingField("code", css_class="col-md-4"),
                ),
                Column(
                    FloatingField("amp", css_class="col-md-2"),
                ),
            ),
            FloatingField("description"),
            Row(
                Column(FloatingField("location", css_class="col-md-4")),
                Column(FloatingField("gps_coordinates", css_class="col-md-2")),
            ),
            Row(
                Column(
                    # NB having datepicker here isn't supposed to be necessary.
                    # But FloatingFields have issues....
                    FloatingField("date_activated", css_class="col-md-4 datepicker")
                ),
                (
                    Column(FloatingField("date_retired", css_class="col-md-4"))
                    if self.existing_site
                    else None
                ),
            ),
        )

        return helper

    def __init__(self, *args, existing_site=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.existing_site = existing_site

        # Make help_texts appear as Bootstrap tooltips
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get("placeholder", ""):
                field.widget.attrs.setdefault("placeholder", field.label)
            if field.help_text:
                field.widget.attrs["title"] = field.help_text
                field.widget.attrs["data-bs-toggle"] = "tooltip"
                field.widget.attrs["data-bs-placement"] = "top"
                # Suppress default help_text rendering
                field.help_text = ""


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["image", "caption"]
