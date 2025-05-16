from django.contrib.auth.forms import password_validation
from django.db.models import Count
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import redirect, render  # , get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.functions import Lower
from urllib.parse import urlencode
from django.urls import reverse_lazy, reverse

from inventory.models import Site, InventoryItem
from .forms import InventoryItemForm, SiteForm, MaintenanceRecordFormSet


def test_html(request):
    class User:
        def __init__(self):
            self.is_authenticated = True
            self.username = "HTML Tester"
            self.is_superuser = True

    print("well well, test_html")
    context = {"user": User()}
    return render(request, "inventory/site_base.html", context)


class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    fields = ["description", "serial_number", "location"]
    template_name = "inventory/lists.html"
    paginate_by = 14
    context_object_name = "table_items"
    _sort_key = "description"

    def get_queryset(self):
        base_qs = InventoryItem.objects.all()
        qs = base_qs

        if not qs.exists():
            messages.info(self.request, "No items are currently in the inventory.")

        # Done this way to ensure the ordering matches the desired
        # order defined in the model Meta class: CHANGE THIS!
        return qs.annotate(maintenance_count=Count("maintenance_records")).order_by(
            *self.model._meta.ordering
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = SiteListView._sort_key
        context["filter_fields"] = [
            {"name": "description", "label": "Description", "type": "text"},
            {"name": "serial_number", "label": "Serial number", "type": "text"},
            {"name": "site", "label": "Site", "type": "text"},
            {"name": "notes", "label": "Notes", "type": "text"},
        ]
        context["table_fields"] = [
            {"name": "description", "label": "Description"},
            {"name": "location", "label": "Site"},
            {"name": "serial_number", "label": "Serial number"},
            {"name": "notes", "label": "Notes"},
        ]
        context["reset_url"] = reverse("home")
        context["add_url"] = reverse("inventory_add")
        context["heading"] = "Inventory"
        context["add_button"] = "Add New Inventory Item"
        context["edit_url"] = "inventory_edit"

        return context


class SiteListView(LoginRequiredMixin, ListView):
    model = Site
    paginate_by = 15
    template_name = "inventory/lists.html"
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "description"

    def _temp(self):
        return super().get_queryset()

    def get_queryset(self):
        # This line results in warnings about unreachable code:
        # qs = super().get_queryset().annotate(item_count=Count("inventory_items"))
        # Doing it this way avoids the warning:
        base_qs = Site.objects.all()
        qs = base_qs.annotate(item_count=Count("inventory_items"))

        if not qs.exists():
            messages.info(self.request, "No sites are currently defined.")

        # Get sort and filter parameters
        description_filter = self.request.GET.get("description", "")
        address_filter = self.request.GET.get("address", "")
        gps_coordinates_filter = self.request.GET.get("gps_coordinates", "")
        item_count_filter = self.request.GET.get("item_count")

        # Apply filters to queryset
        if description_filter:
            qs = qs.filter(description__icontains=description_filter)
        if address_filter:
            qs = qs.filter(address__icontains=address_filter)
        if gps_coordinates_filter:
            qs = qs.filter(gps_coordinates__icontains=gps_coordinates_filter)
        if item_count_filter:
            try:
                qs = qs.filter(item_count=int(item_count_filter))
            except ValueError:
                pass  # Ignore invalid input

        # Apply sorting
        sort = self.request.GET.get("sort", SiteListView._sort_key)
        SiteListView._sort_key = sort

        if sort.lstrip("-") in [
            "description",
            "address",
            "gps_coordinates",
            "id",
            "item_count",
        ]:
            if sort.startswith("-"):
                qs = qs.order_by(Lower(sort[1:]).desc())
            else:
                qs = qs.order_by(Lower(sort))

        return qs.annotate(item_count=Count("inventory_items"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = SiteListView._sort_key
        context["filter_fields"] = [
            {"name": "description", "label": "Name", "type": "text"},
            {"name": "address", "label": "Address", "type": "text"},
        ]
        context["table_fields"] = [
            {"name": "description", "label": "Name"},
            {"name": "address", "label": "Address"},
            {"name": "gps_coordinates", "label": "GPS"},
            {"name": "item_count", "label": "Items"},
        ]
        context["reset_url"] = reverse("view_sites")
        context["add_url"] = reverse("add_site")
        context["heading"] = "Sites"
        context["add_button"] = "Add New Site"
        context["edit_url"] = "edit_site"

        return context


class InventoryItemCreateView(CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_detail.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.success(self.request, "Inventory item added successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Returns a dict with keys, 'object', 'site', 'form', 'view'.

        Each of those items is available under that name in template."""
        context_data = super().get_context_data(**kwargs)
        context_data["cancel_url"] = reverse("home")
        context_data["action"] = "New"
        print(context_data)

        return context_data


class InventoryItemUpdateView(UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_detail.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["cancel_url"] = reverse("home")
        context_data["action"] = "Edit"

        if self.request.POST:
            context_data["formset"] = MaintenanceRecordFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context_data["formset"] = MaintenanceRecordFormSet(instance=self.object)
        return context_data

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


class SiteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Site
    success_url = reverse_lazy("view_sites")
    success_message = "Site %(description)s was deleted successfully!"

    # Can use this to protect agains deleting a location holding
    # inventory items:
    # def post(self, request, *args, **kwargs):
    #     location = self.get_object()
    #     if location.inventory_items.exists():
    #         messages.error(
    #             request, "Cannot delete this location — it still has inventory items."
    #         )
    #         return HttpResponseRedirect(
    #             location.get_absolute_url()
    #         )  # Or wherever your edit page is
    #     return super().post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Location was successfully deleted.")
        return super().delete(request, *args, **kwargs)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            description=self.object.description,
        )


class SiteCreateView(LoginRequiredMixin, CreateView):
    model = Site
    form_class = SiteForm
    template_name = "inventory/site_detail.html"
    success_url = reverse_lazy("view_sites")

    def get_context_data(self, **kwargs):
        """Returns a dict with keys, 'object', 'site', 'form', 'view'.

        Each of those items is available under that name in template."""
        context_data = super().get_context_data(**kwargs)
        context_data["cancel_url"] = reverse("view_sites")
        context_data["action"] = "New"

        # ADD PHOTOS here
        return context_data


class SiteUpdateView(LoginRequiredMixin, UpdateView):
    model = Site
    form_class = SiteForm
    template_name = "inventory/site_detail.html"
    success_url = reverse_lazy("view_sites")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["cancel_url"] = reverse("view_sites")
        context_data["action"] = "Edit"
        context_data["delete_url"] = reverse(
            "delete_site",
            args=[
                self.object.id,
            ],
        )
        context_data["items"] = self.object.inventory_items.all()
        # ADD PHOTOS here
        return context_data


def logout_view(request):
    logout(request)
