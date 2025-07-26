from django import forms
from django.template.loader import render_to_string
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    # ButtonHolder,
    Layout,
    Field,
    Row,
    Column,
    LayoutObject,
    # Submit,
)
from crispy_forms.layout import HTML

# from crispy_bootstrap5.bootstrap5 import FloatingField

from .models import (
    Site,
    DOI,
    # Photo,
    FieldNote,
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
        )

        return helper

    def __init__(self, *args, existing_site=None, cancel_url=None, **kwargs):
        if existing_site is None:
            raise ValueError(
                "SiteForm must be initalized with existing_site=True|False"
            )
        super().__init__(*args, **kwargs)
        self.existing_site = existing_site
        self.cancel_url = cancel_url
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


# FieldNotes
class FieldNoteForm(forms.ModelForm):
    class Meta:
        model = FieldNote
        fields = ["site", "note", "submitter", "date_submitted", "summary"]

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_fieldnote_form"
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
                Column(Field("site"), css_class="col-md-4", label="Site"),
                Column(
                    Field("submitter"),
                    css_class="col-md-4",
                    label="Submitted by",
                ),
                Column(Field("date_submitted", css_class="col-md-2  datepicker")),
                css_class="mb-1",
            ),
            Row(
                Field("note", rows=20),
                css_class="mb-1",
            ),
            Row(
                Field(
                    "summary",
                ),
                css_class="mb-1",
            ),
        )

        return helper

    def __init__(self, *args, site_id=None, cancel_url=None, **kwargs):
        super().__init__(*args, **kwargs)
        if site_id:
            self.fields["site"].initial = Site.objects.get(pk=site_id)
        self.site_id = site_id
        self.cancel_url = cancel_url
        self.helper = self.__init_FormHelper()
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


# # photos
# class PhotoForm(forms.ModelForm):
#     class Meta:
#         model = Photo
#         fields = ["image", "caption"]


# PhotoFormSet = inlineformset_factory(
#     Site, Photo, form=PhotoForm, extra=1, can_delete=True
# )


# DOI links
class DOIForm(forms.ModelForm):
    class Meta:
        model = DOI
        fields = ["label", "doi_link"]
        labels = {
            "doi_link": "DOI link",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = (
            False  # the <form> and Submit buttons are in the parent template
        )
        self.helper.layout = Layout(
            Row(
                Column(Field("label", wrapper_class="mb-0"), css_class="col-3"),
                Column(Field("doi_link", wrapper_class="mb-0"), css_class="col-7"),
                Column(
                    Field("DELETE", type="hidden"),  # Hidden delete field
                    HTML(
                        """
                      <button type="button"
                              class="btn btn-danger btn-sm remove-form-row"
                              title=" Remove"
                              data-confirm="Are you sure you want to remove this DOI record?">
                        <i class="bi bi-trash"></i> Remove
                      </button>
                    """
                    ),
                    css_class="col-auto d-flex mt-4 align-items-center",
                ),
                css_class="g-2 align-items-center",
            )
        )


class BaseDOIFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if form.cleaned_data.get("DELETE", False):
                continue
            if form.has_changed():
                # Force validation even if not already done
                form.full_clean()
                if not form.is_valid():
                    raise ValidationError("Incomplete or invalid DOI record.")


class StrictDOIFormSet(BaseDOIFormSet):
    pass


DOIFormSet = inlineformset_factory(
    Site,
    DOI,
    form=DOIForm,
    formset=StrictDOIFormSet,
    fields=[
        "label",
        "doi_link",
    ],  # List all editable DOI fields here
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=True,
)
