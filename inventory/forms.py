from django import forms

# from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column
from crispy_forms.layout import HTML

# from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import (
    Site,
    # DOI,
    # Photo,
    # FieldNote,
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

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_create_site"
        helper.form_method = "POST"
        # multipart/form-data is automatically set when the form needs
        # this enctype, so there is no official helper attribute for it.
        helper.form_class = "track-unsaved form-class"
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"  # auto-width for inputs
        helper.attrs = {"novalidate": ""}
        helper.layout = Layout(
            Row(
                Column(Field("name"), css_class="col-md-6"),
                Column(Field("code"), css_class="col-md-4"),
                Column(Field("amp"), css_class="col-md-2"),
                css_class="mb-1",
            ),
            Row(
                Column(Field("description"), css_class="col-6"),
                Column(Field("location"), css_class="col-md-4"),
                Column(Field("gps_coordinates"), css_class="col-md-2"),
                css_class="mb-1",
            ),
            Row(
                Column(Field("date_activated", css_class="col-md-2  datepicker")),
                (
                    Column(Field("date_retired", css_class="col-md-4 datepicker"))
                    if self.existing_site
                    else None
                ),
                css_class="mb-1",
            ),
            # Submit/Cancel/Delete Buttons
            Row(
                Column(
                    HTML(
                        """<button type="submit" class="btn btn-primary me-2">
                    <i class="bi bi-check-circle me-2"></i>Save
                    </button>
                    """
                    ),
                    HTML(
                        f"""<a class="btn btn-secondary" href={self.cancel_url}>
                        <i class="bi bi-trash me-2"></i>Cancel</a>"""
                    ),
                    # DELETE button goes here, then move helper
                    # creation to a separate class or mixin
                    css_class="d-flex justify-content-start mt-3",
                )
            ),
        )
        return helper

    def __init__(self, *args, existing_site=True, cancel_url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_site = existing_site
        self.cancel_url = cancel_url
        self.helper = self.__init_FormHelper()
        self.fields["name"].widget.attrs["size"] = self.fields["name"].max_length
        self.fields["code"].widget.attrs["size"] = self.fields["code"].max_length
        self.fields["amp"].widget.attrs["size"] = self.fields["amp"].max_length
        self.fields["location"].widget.attrs["size"] = self.fields[
            "location"
        ].max_length
        # Make help_texts appear as Bootstrap tooltips
        for field_name, field in self.fields.items():
            # if not field.widget.attrs.get("placeholder", ""):
            #     field.widget.attrs.setdefault("placeholder", field.label)
            if field.help_text:
                field.widget.attrs["title"] = field.help_text
                field.widget.attrs["data-bs-toggle"] = "tooltip"
                field.widget.attrs["data-bs-placement"] = "top"
                # Suppress default help_text rendering
                # field.help_text = ""


# # FieldNotes
# class FieldNoteForm(forms.ModelForm):
#     class Meta:
#         model = FieldNote
#         fields = ["note", "user", "uploaded_at"]


# FieldNoteFormSet = inlineformset_factory(
#     Site, FieldNote, form=FieldNoteForm, extra=1, can_delete=True
# )


# # photos
# class PhotoForm(forms.ModelForm):
#     class Meta:
#         model = Photo
#         fields = ["image", "caption"]


# PhotoFormSet = inlineformset_factory(
#     Site, Photo, form=PhotoForm, extra=1, can_delete=True
# )


# # DOI links
# class DOIForm(forms.ModelForm):
#     class Meta:
#         model = DOI
#         fields = ["label", "doi_link"]
#         labels = {
#             "doi_link": "DOI link",
#         }


# DOIFormSet = inlineformset_factory(Site, DOI, form=DOIForm, extra=1, can_delete=True)


# class DOIFormSetHelper(FormHelper):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.form_tag = False
#         self.layout = Layout(
#             Row(
#                 Column(FloatingField("label"), css_class="col-md-4"),
#                 Column(FloatingField("doi_link"), css_class="col-md-4"),
#                 css_class="mb-2",
#             )
#         )


# class SiteFormHelper(FormHelper):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.form_tag = False

#         # self.form_id = 'some-id'
#         self.form_method = "post"
#         self.form_action = "sites"
#         self.layout = Layout(
