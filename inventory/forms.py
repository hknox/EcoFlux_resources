from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Field,
    Row,
    Column,
    HTML,
    Submit,
    Div,
)

from .models import Equipment, Site, FieldNote, Photo, Document


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
        labels = {"amp": "AMP"}

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_site_form"
        helper.form_method = "POST"
        helper.form_tag = False
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"  # auto-width for inputs
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
                Column(Field("date_activated", css_class="col-md-2 datepicker")),
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
        self.helper = self.__init_FormHelper()
        # TODO Are these useful?
        self.fields["name"].widget.attrs["size"] = self.fields["name"].max_length
        self.fields["code"].widget.attrs["size"] = self.fields["code"].max_length
        self.fields["amp"].widget.attrs["size"] = self.fields["amp"].max_length
        self.fields["location"].widget.attrs["size"] = self.fields[
            "location"
        ].max_length
        # TODO move this to a common mixin?
        #      or add a simple function to this module and call it?
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
        fields = [
            "site",
            "note",
            "submitter",
            "date_visited",
            "summary",
            "site_visitors",
        ]

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_fieldnote_form"
        helper.form_method = "POST"
        helper.form_tag = False
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"  # auto-width for inputs
        helper.layout = Layout(
            Row(
                Column(Field("site"), css_class="col-md-4"),
                Column(
                    Field("submitter"),
                    css_class="col-md-4",
                    label="Submitted by",
                ),
                Column(Field("date_visited", css_class="col-md-2 datepicker")),
                css_class="mb-1",
            ),
            Row(
                Field("site_visitors"),
                css_class="mb-1",
            ),
            Row(
                Field("note", rows=12),
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
            self.fields["site"].disabled = True
        self.site_id = site_id
        self.fields["site"].empty_label = "--Select a site--"
        self.helper = self.__init_FormHelper()
        # TODO move this to a common mixin?
        #      or add a simple function to this module and call it?
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


# Equipment
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            "instrument",
            "manufacturer",
            "model_number",
            "serial_number",
            "date_purchased",
            "notes",
            "site",
        ]

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_equipment_form"
        helper.form_method = "POST"
        helper.form_tag = False
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"
        helper.layout = Layout(
            Row(
                Column(Field("instrument"), css_class="col-md-6"),
                Column(Field("manufacturer"), css_class="col-md-6"),
                css_class="mb-1",
            ),
            Row(
                Column(
                    Field("model_number"),
                    css_class="col-md-6",
                ),
                Column(Field("serial_number", css_class="col-md-6")),
                css_class="mb-1",
            ),
            Row(
                Column(
                    Field("site"),
                    css_class="col-md-6",
                ),
                Column(
                    Field("date_purchased", css_class="datepicker"),
                ),
                css_class="mb-1",
            ),
            Row(
                Field("notes", rows=6),
                css_class="mb-1",
            ),
        )

        return helper

    def __init__(self, *args, site_id=None, cancel_url=None, **kwargs):
        # def __init__(self, cancel_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if site_id:
            self.fields["site"].initial = Site.objects.get(pk=site_id)
            self.fields["site"].disabled = True
        self.site_id = site_id
        self.helper = self.__init_FormHelper()
        self.fields["site"].empty_label = "--Select a site--"
        # TODO move this to a common mixin?
        #      or add a simple function to this module and call it?
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


# documents
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "submitter",
            "date_uploaded",
            "date_received",
            "summary",
            "file",
        ]
        labels = {
            "submitter": "Submitted by",
            "summary": "Short descriptive summary",
            "file": "Document",
        }
        widgets = {
            "date_uploaded": forms.DateInput(
                attrs={"placeholder": "Select a date", "class": "flatpickr"}
            ),
            "date_received": forms.DateInput(attrs={"class": "flatpickr"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.attrs = {"enctype": "multipart/form-data"}
        self.helper.layout = Layout(
            Row(
                Column("submitter", css_class="col-md-6"),
                Column("date_uploaded", css_class="col-md-3"),
            ),
            Div(
                HTML(
                    """ <div id="drop-zone" class="border border-secondary rounded p-5 text-center bg-light" style="cursor:pointer;">
                    <p class="mb-0">Drag & drop a PDF document here or click to select one</p>
                    </div>
                    <input type="file" name="file" id="id_document" style="display:none;" accept="application/pdf,.pdf">
                    """
                ),
                css_class="mb-3",
            ),
            Row(
                Column("summary", css_class="col-md-6"),
                Column("date_received", css_class="col-md-3"),
            ),
            Div(
                Submit("submit", "Upload Document", css_class="btn btn-primary"),
                HTML(
                    '<a href="{{ cancel_url }}" class="btn btn-secondary ms-2 btn-cancel">Cancel</a>'
                ),
                css_class="mt-3",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        file = cleaned_data.get("file")
        if not file:
            raise forms.ValidationError("Please select a file to upload.")

        return cleaned_data


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["date_received", "summary"]

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_document_form"
        helper.form_method = "POST"
        helper.form_tag = False
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"
        helper.layout = Layout(
            Row(
                Column(Field("date_received"), css_class="col-md-4"),
                Column(
                    Field("summary"),
                ),
                css_class="mb-1",
            ),
        )
        return helper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = self.__init_FormHelper()
        self.fields["date_received"].widget.attrs["class"] = "datepicker"


# photos
class MultiFileInput(forms.ClearableFileInput):
    """Widget that allows selecting multiple files."""

    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    """
    A FileField that accepts multiple files and returns them as a list.
    """

    # widget = MultiFileInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultiFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            raise forms.ValidationError("Please select at least one image file.")

        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class PhotoUploadForm(forms.Form):
    taken_by = forms.CharField(
        required=True,
        label="Batch taken by",
        max_length=100,
    )
    date_taken = forms.DateField(
        required=True,
        label="Date batch taken",
        widget=forms.DateInput(
            attrs={
                "placeholder": "Select a date",
                "class": "flatpickr",
            }
        ),
    )
    photos = MultiFileField(
        required=True,
        label="",
        help_text="You can select one or more image files.",
        widget=MultiFileInput(
            attrs={
                "id": "id_photos",
                "required": True,
                "style": "display:none;",
                "accept": "image/*,.jpg,.jpeg,.png",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.attrs = {"enctype": "multipart/form-data"}
        self.helper.layout = Layout(
            Div(
                HTML("""
                    <div id="drop-zone" class="border border-secondary rounded p-5 text-center bg-light" style="cursor:pointer;">
                        <p class="mb-0">Drag & drop photos here or click to select</p>
                    </div>
                    <div id="preview" class="d-flex flex-wrap mt-3"></div>
                """),
                # hidden input triggered by JS:
                "photos",  # simpler than Field("photos");
                css_class="mt-3",
            ),
            Row(
                Column("taken_by", css_class="col-md-6"),
                Column("date_taken", css_class="col-md-6"),
                css_class="mb-2",
            ),
            Div(
                Submit("submit", "Upload Photos", css_class="btn btn-primary"),
                HTML(
                    '<a href="{{ cancel_url }}" class="btn btn-secondary ms-2 btn-cancel">Cancel</a>'
                ),
            ),
        )

    def clean_photos(self):
        files = self.files.getlist("photos")

        if not files:
            raise forms.ValidationError("Please select at least one image file.")
        for f in files:
            if not f.content_type.startswith("image/"):
                raise forms.ValidationError(f"'{f.name}' is not a valid image file.")

        return files


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ["date_taken", "taken_by"]

    def __init_FormHelper(self):
        helper = FormHelper()
        helper.form_id = "id_photo_form"
        helper.form_method = "POST"
        helper.form_tag = False
        helper.label_class = (
            "col-auto col-form-label text-end align-self-center py-0 pe-2 label-class"
        )
        helper.field_class = "col-auto field-class"
        helper.layout = Layout(
            Row(
                Column(Field("taken_by"), css_class="col-md-6"),
                Column(Field("date_taken"), css_class="col-md-6"),
                css_class="mb-1",
            ),
        )
        return helper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = self.__init_FormHelper()
        self.fields["date_taken"].widget.attrs["class"] = "datepicker"
