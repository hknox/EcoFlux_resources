# from django.contrib.auth.forms import password_validation
# from django.db.models import Count
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import redirect, render  # get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.functions import Lower
from django.urls import reverse_lazy, reverse

from inventory.models import Site  # ,Photo  # ,InventoryItem
from .forms import (
    SiteForm,
    DOIFormSet,
    # DOIFormSetHelper,
    # fieldnoteformset,
    # PhotoFormSet,
    # PhotoFormSetHelper,
)


def EndOfInternet(request):
    return redirect("https://hmpg.net/")


def logout_view(request):
    logout(request)


class SiteViewsMixin:
    model = Site
    form_class = SiteForm
    template_name = "inventory/site_detail.html"
    success_url = reverse_lazy("view_sites")
    cancel_url = reverse_lazy("view_sites")

    def initialize_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.cancel_url

        return context

    def handle_post(self, request, *args, **kwargs):
        # Construct form and formset here
        form = self.get_form()
        if self.object == None:
            # New site
            formset = DOIFormSet(request.POST)
        else:
            # Existing site
            formset = DOIFormSet(request.POST, instance=self.object)

        # Store for use in get_context_data()
        self._form = form
        self._formset = formset

        if form.is_valid() and formset.is_valid():
            site = form.save()
            formset.instance = site
            formset.save()
            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data())

    # def form_valid(self, form):
    #     """You can safely delete this form_valid() method if you’re not
    #     using Django’s built-in form-handling flow (i.e., if you’re
    #     manually handling POST requests in your own post() method as shown
    #     earlier). Why?

    #     The form_valid method is part of Django’s generic class-based
    #     view workflow. If you override post() and handle all form and
    #     formset logic there (including saving and redirecting), Django
    #     will not call form_valid. Your logic in post() takes
    #     precedence.

    #     When would you need form_valid? If you rely on the default CBV
    #     flow (don’t override post()), you would only need to override
    #     form_valid to add formset-handling logic after the parent form
    #     is saved.
    #     """


class SiteCreateView(LoginRequiredMixin, SiteViewsMixin, CreateView):

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = "New "

        # Use cached versions if present (from POST)
        context["form"] = getattr(self, "_form", self.get_form())
        context["doi_formset"] = getattr(self, "_formset", DOIFormSet())

        return context

    def post(self, request, *args, **kwargs):
        self.object = None  # Required for CreateView
        return self.handle_post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Let the form know this is a NEW site
        kwargs["existing_site"] = False
        return kwargs


class SiteUpdateView(LoginRequiredMixin, SiteViewsMixin, UpdateView):

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = "Edit "
        delete_url = reverse(
            "delete_site",
            args=[
                context["object"].id,
            ],
        )
        context["delete_url"] = delete_url

        context["form"] = getattr(self, "_form", self.get_form())
        context["doi_formset"] = getattr(
            self, "_formset", DOIFormSet(instance=self.get_object())
        )

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Required for UpdateView
        return self.handle_post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Let the form know this is an EXISTING site
        kwargs["existing_site"] = True
        return kwargs


class SiteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Site
    success_url = reverse_lazy("view_sites")
    success_message = "Site %(description)s was deleted successfully!"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Location was successfully deleted.")
        return super().delete(request, *args, **kwargs)

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            description=self.object.description,
        )

    # Can eventually use this to protect agains deleting a location
    # holding inventory items:
    #
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

        field_list = [field["name"] for field in self.sort_fields]
        if sort.lstrip("-") in field_list:
            if sort.startswith("-"):
                print(f"BB-de: {sort}, {sort[1:]}")
                queryset = queryset.order_by(Lower(sort[1:]).desc())
            else:
                print(f"BB-as: {sort}")
                queryset = queryset.order_by(Lower(sort))

        return queryset


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
    display_fields = [
        {"name": "name", "label": "Name"},
        {"name": "code", "label": "Code"},
    ]

    def get_queryset(self):
        # This line results in warnings about unreachable code:
        # qs = super().get_queryset().annotate(item_count=Count("inventory_items"))
        # Doing it this way avoids the warning:
        base_qs = Site.objects.all()
        qs = base_qs  # .annotate(item_count=Count("inventory_items"))

        if not qs.exists():
            messages.info(self.request, "No sites are currently defined.")
            return qs

        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs  # .annotate(item_count=Count("inventory_items"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.sort_fields
        context["sorted_fields"] = self.sort_fields
        context["reset_url"] = reverse("view_sites")
        context["add_url"] = reverse("add_site")
        context["heading"] = "Sites"
        context["add_button"] = "Add New Site"
        context["edit_url"] = "edit_site"

        return context


# def upload_photo_from_site(request, site_id):
#     site = get_object_or_404(Site, id=site_id)
#     if request.method == "POST":
#         form = PhotoForm(request.POST, request.FILES)
#         if form.is_valid():
#             photo = form.save(commit=False)
#             photo.site = site
#             photo.save()
#             return redirect("site_detail", site_id=site.id)
#     else:
#         form = PhotoForm()
#     return render(request, "upload_photo.html", {"form": form, "site": site})


def upload_photo(request):
    if request.method == "POST":
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.site = site
            photo.save()
            return redirect("site_detail", site_id=site.id)
    else:
        form = PhotoForm()

    return render(request, "upload_photo.html", {"form": form})


def test_html(request):
    class User:
        def __init__(self):
            self.is_authenticated = True
            self.username = "HTML Tester"
            self.is_superuser = True

    print("well well, test_html")
    context = {"user": User(), "heading": "Photos"}
    return render(request, "inventory/photos.html", context)
