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

class SortedListView(ListView):
    """Add persistent sort machinery to ListView"""

    lookup_default = "icontains"

    def apply_filters(self, queryset):

        for field_filter in self.filter_fields:
            raw_value = self.request.GET.get(field_filter["name"], "").strip()
            if not raw_value:
                continue

            # Determine the base lookup path (e.g., location__description)
            field_name = field_filter.get("lookup", field_filter["name"])
            lookup_type = field_filter.get("lookup_type", self.lookup_default)
            filter_key = f"{field_name}__{lookup_type}"
            # Convert numbers safely
            if field_filter["type"] == "number":
                try:
                    raw_value = int(raw_value)
                except ValueError:
                    continue
            queryset = queryset.filter(**{filter_key: raw_value})

        return queryset

    def apply_sort_parameters(self, queryset):
        sort = self.request.GET.get("sort", self._sort_key)
        self._sort_key = sort
        print(sort)

        field_list = [field["name"] for field in self.sort_fields]
        if sort.lstrip("-") in field_list:
            if sort.startswith("-"):
                print(f"BB-de: {sort}, {sort[1:]}")
                queryset = queryset.order_by(Lower(sort[1:]).desc())
            else:
                print(f"BB-as: {sort}")
                queryset = queryset.order_by(Lower(sort))

        return queryset


class InventoryListView(LoginRequiredMixin, SortedListView):
    model = InventoryItem
    template_name = "inventory/lists.html"
    paginate_by = 14
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "description"

    filter_fields = [
        {"name": "description", "label": "Description", "type": "text"},
        {"name": "serial_number", "label": "Serial number", "type": "text"},
        {
            "name": "location",
            "label": "Site",
            "type": "text",
            "lookup": "location__description",
        },
        {"name": "notes", "label": "Notes", "type": "text"},
        # {"name": "date_purchased_start", "label": "Purchased After", "type": "date", "lookup": "date_purchased", "lookup_type": "gte"},
        # {"name": "date_purchased_end", "label": "Purchased Before", "type": "date", "lookup": "date_purchased", "lookup_type": "lte"},
        {
            "name": "maintenance_count_min",
            "label": "Min Maintenance Records",
            "type": "number",
            "lookup": "maintenance_count",
            "lookup_type": "gte",
        },
        # {
        #     "name": "maintenance_count_max",
        #     "label": "Max Maintenance Records",
        #     "type": "number",
        #     "lookup": "maintenance_count",
        #     "lookup_type": "lte",
        # },
    ]
    sort_fields = [
        {"name": "description", "label": "Description"},
        {"name": "location", "label": "Location"},
        {"name": "serial_number", "label": "Serial number"},
        {"name": "notes", "label": "Notes"},
    ]

    def get_queryset(self):
        qs = InventoryItem.objects.all()

        if not qs.exists():
            messages.info(self.request, "No items are currently in the inventory.")
            return qs

        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs.annotate(maintenance_count=Count("maintenance_records"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.sort_fields
        context["reset_url"] = reverse("home")
        context["add_url"] = reverse("inventory_add")
        context["heading"] = "Inventory"
        context["add_button"] = "Add New Inventory Item"
        context["edit_url"] = "inventory_edit"

        return context


class SiteListView(LoginRequiredMixin, SortedListView):
    model = Site
    paginate_by = 14
    template_name = "inventory/lists.html"
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "description"
    filter_fields = [
        {"name": "description", "label": "Name"},
        {"name": "address", "label": "Address"},
        {"name": "gps_coordinates", "label": "GPS"},
        {
            "name": "item_count_min",
            "label": "Min. Item Count",
            "type": "number",
            "lookup": "item_count",
            "lookup_type": "gte",
        },
        # This one needs to account for int type, and maybe < or >
        # {"name": "item_count", "label": "Items"},
    ]
    sort_fields = [
        {"name": "description", "label": "Name"},
        {"name": "address", "label": "Address"},
        {"name": "gps_coordinates", "label": "GPS"},
        {"name": "item_count", "label": "Items"},
    ]

    def get_queryset(self):
        # This line results in warnings about unreachable code:
        # qs = super().get_queryset().annotate(item_count=Count("inventory_items"))
        # Doing it this way avoids the warning:
        base_qs = Site.objects.all()
        qs = base_qs.annotate(item_count=Count("inventory_items"))

        if not qs.exists():
            messages.info(self.request, "No sites are currently defined.")
            return qs

        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs.annotate(item_count=Count("inventory_items"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.sort_fields
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
