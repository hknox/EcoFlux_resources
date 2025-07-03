from django import forms
from django.template.loader import render_to_string

# from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    ButtonHolder,
    Layout,
    Field,
    Row,
    Column,
    LayoutObject,
    Submit,
)
from crispy_forms.layout import HTML

# from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import (
    Site,
    # DOI,
    # Photo,
    # FieldNote,
)


class DeleteButton(LayoutObject):
    """
    Crispy layout object that renders a standalone Delete button
    meant to go outside the main form, using JavaScript to POST.
    """

    def __init__(
        self,
        delete_url=None,
        label="Delete",
        icon="bi-trash",
        # css_class="btn btn-danger",
        css_class="",
    ):
        self.template = "inventory/crispy_delete_button.html"
        self.delete_url = delete_url
        self.label = label
        self.icon = icon
        self.css_class = css_class

    def render(self, form, context, template_pack="bootstrap5"):
        """ChatGPT had a form_style argument after form which is unused now"""
        context.update(
            {
                "delete_url": self.delete_url,
                "label": self.label,
                "icon": self.icon,
                "css_class": self.css_class,
                "csrf_token": context.get("csrf_token"),
            }
        )
        return render_to_string(self.template, context.flatten())


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
        helper.form_id = "id_site_form"
        helper.form_method = "POST"
        helper.form_tag = False
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
                Column(Field("description", rows=4), css_class="col-6"),
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
            ButtonHolder(
                Submit("submit", "Save", css_class="btn btn-primary"),
                HTML(
                    f"""
                <a href="{{{{ cancel_url }}}}" class="btn btn-secondary btn-cancel">
                <i class="bi bi-x-circle"></i> Cancel
                </a>
                """
                ),
                *([DeleteButton(self.delete_url)] if self.delete_url else []),
            ),
        )

        return helper

    def __init__(
        self, *args, existing_site=True, cancel_url=None, delete_url=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.existing_site = existing_site
        self.cancel_url = cancel_url
        self.delete_url = delete_url
        self.helper = self.__init_FormHelper()
        # Are these useful?
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
