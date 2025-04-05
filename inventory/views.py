from django.db.models import Count
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import redirect  # render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

# from django.contrib.auth.decorators import login_required

from inventory.models import Location, InventoryItem
from .forms import InventoryItemForm, MaintenanceRecordFormSet


class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    fields = ["description", "serial_number", "location"]
    template_name = "inventory/inventory_list.html"
    paginate_by = 14
    context_object_name = "inventory_list"

    def get_queryset(self):
        qs = InventoryItem.objects
        if len(qs.all()) == 0:
            messages.info(self.request, "No inventory items entered.")
        # Done this way to ensure the ordering matches the desired
        # order defined in the model Meta class:
        return qs.annotate(maintenance_count=Count("maintenance_records")).order_by(
            *self.model._meta.ordering
        )


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    paginate_by = 14
    template_name = "inventory/location_list.html"

    def get_queryset(self):
        qs = Location.objects
        if len(qs.all()) == 0:
            messages.info(self.request, "No locations entered.")
        return qs.annotate(item_count=Count("inventory_items")).order_by("pk")

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # add to context as needed...
    #     return context


class InventoryItemCreateView(CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/inventory_item_form.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.success(self.request, "Inventory item added successfully!")
        return super().form_valid(form)


class InventoryItemUpdateView(UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/inventory_item_form.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = MaintenanceRecordFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context["formset"] = MaintenanceRecordFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]

        if form.is_valid() and formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(
                self.request,
                "Inventory item and maintenance records updated successfully.",
            )
            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data(form=form))


class LocationDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Location
    fields = ["description", "address", "gps_coordinates"]
    template_name_suffix = "_delete_form"
    success_url = reverse_lazy("view_locations")
    success_message = "Location %(description)s was deleted successfully!"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            description=self.object.description,
        )


class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    fields = ["description", "address", "gps_coordinates"]
    template_name_suffix = "_detail_form"
    success_url = reverse_lazy("view_locations")


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    fields = ["description", "address", "gps_coordinates"]
    template_name_suffix = "_detail_form"
    success_url = reverse_lazy("view_locations")


def logout_view(request):
    logout(request)
