from django import forms
from django.forms import inlineformset_factory

from .models import Site, InventoryItem, MaintenanceRecord


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            "description",
            "code",
            "date_activated",
            "address",
            "gps_coordinates",
        ]
        widgets = {
            "date_activated": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",  # "datepicker" for JS hook, "form-control" for Bootstrap
                    "placeholder": "YYYY-MM-DD",  # Needed for floating label
                    "autocomplete": "off",
                }
            ),
        }


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["description", "serial_number", "date_purchased", "location", "notes"]
        widgets = {
            "location": forms.Select(attrs={"class": "form-select"}),
            "date_purchased": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",
                    "placeholder": "YYYY-MM-DD",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the location dropdown dynamically
        self.fields["location"].queryset = Site.objects.all()
        self.fields["location"].empty_label = "Select a Location"  # Placeholder option


class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ["date", "description"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "class": "form-control datepicker",
                    "placeholder": "YYYY-MM-DD",
                }
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control"}
            ),  # Single-line text input
        }


MaintenanceRecordFormSet = inlineformset_factory(
    InventoryItem,
    MaintenanceRecord,
    form=MaintenanceRecordForm,
    extra=0,  # Don't add extra forms by default, we'll add via JavaScript
    can_delete=True,  # Allows deleting existing records
)


class OneToOneTableForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ["description"]
