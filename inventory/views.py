# from django.contrib.auth.forms import password_validation
from django.db.models import Case, When, Value, CharField, Count
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import redirect, render  # get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.functions import Lower
from django.urls import reverse_lazy, reverse

from inventory.models import Site, FieldNote, Equipment  # ,Photo
from .forms import (
    HistoryFormSet,
    SiteForm,
    DOIFormSet,
    FieldNoteForm,
    EquipmentForm,
    # PhotoFormSet,
)


def EndOfInternet(request):
    return redirect("https://hmpg.net/")


class EquipmentViewsMixin:
    model = Equipment
    form_class = EquipmentForm
    template_name = "inventory/equipment_detail.html"
    success_url = reverse_lazy("view_equipment")
    cancel_url = reverse_lazy("view_equipment")

    def initialize_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.cancel_url

        return context

    def handle_post(self, request, *args, **kwargs):
        # Construct form and formset here
        form = self.get_form()
        if self.object == None:
            # New site
            formset = HistoryFormSet(request.POST)
        else:
            # Existing site
            formset = HistoryFormSet(request.POST, instance=self.object)

        # Store for use in get_context_data()
        self._form = form
        self._formset = formset

        if form.is_valid() and formset.is_valid():
            site = form.save()
            formset.instance = site
            formset.save()
            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data())


class EquipmentCreateView(LoginRequiredMixin, EquipmentViewsMixin, CreateView):

    def get_context_data(self, **kwargs):
        context_data = self.initialize_context_data(**kwargs)
        context_data["action"] = "New"
        return context_data


class EquipmentUpdateView(LoginRequiredMixin, EquipmentViewsMixin, UpdateView):

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = "Edit "
        delete_url = reverse(
            "site_delete",
            args=[
                context["object"].id,
            ],
        )
        context["delete_url"] = delete_url
        context["form"] = getattr(self, "_form", self.get_form())
        context["history_formset"] = getattr(
            self, "_formset", HistoryFormSet(instance=self.get_object())
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Required for UpdateView
        return self.handle_post(request, *args, **kwargs)


class FieldNoteCreateView(LoginRequiredMixin, CreateView):
    model = FieldNote
    form_class = FieldNoteForm
    template_name = "inventory/fieldnote.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.request.GET.get(
            "next", reverse_lazy("view_fieldnotes")
        )

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["site_id"] = self.request.GET.get("site")

        return kwargs

    def get_success_url(self):
        return self.request.GET.get("next", reverse_lazy("view_fieldnotes"))


class FieldNoteUpdateView(LoginRequiredMixin, UpdateView):
    model = FieldNote
    form_class = FieldNoteForm
    template_name = "inventory/fieldnote.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.request.GET.get(
            "next", reverse_lazy("view_fieldnotes")
        )
        delete_url = reverse(
            "fieldnote_delete",
            args=[
                context["object"].id,
            ],
        )
        context["delete_url"] = delete_url
        return context

    def get_success_url(self):
        return self.request.GET.get("next", reverse_lazy("view_fieldnotes"))


class FieldNoteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = FieldNote
    success_url = reverse_lazy("view_fieldnotes")
    success_message = (
        "Field note of %(date)s for site %(site)s was deleted successfully!"
    )

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            date=self.object.date_submitted,
            site=self.object.site,
        )


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
            "site_delete",
            args=[
                context["object"].id,
            ],
        )
        context["delete_url"] = delete_url

        context["form"] = getattr(self, "_form", self.get_form())
        context["doi_formset"] = getattr(
            self, "_formset", DOIFormSet(instance=self.get_object())
        )
        context["fieldnotes"] = self.object.fieldnotes.order_by("date_submitted")

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
    success_message = "Site %(code)s: %(name)s was deleted successfully!"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            code=self.object.code,
            name=self.object.name,
        )

    # Can eventually use this to protect agains deleting a location
    # holding inventory items:
    #
    # def post(self, request, *args, **kwargs):
    #     location = self.get_object()
    #     if location.inventory.exists():
    #         messages.error(
    #             request, "Cannot delete this location — it still has inventory items."
    #         )
    #         return HttpResponseRedirect(
    #             location.get_absolute_url()
    #         )  # Or wherever your edit page is
    #     return super().post(request, *args, **kwargs)


class SortedListMixin(ListView):
    """Add persistent sort machinery to ListView.

    Pass a table_fields list of dicts for the template via the context
    to control display of headers and data, eg:

    table_fields = [
        {"name": "date_submitted", "label": "Date submitted"},
        {"name": "site", "label": "Site"},
        {"name": "display_summary", "label": # "Summary"},
    ]

    Use extra keys for more control:
    - "sortable": if "no", don't offer sort arrows on the column header.
    - "max_chars": truncate the data to max_chars number of characters.
    """

    lookup_default = "icontains"
    # Default maximum field width
    _default_max_chars = 50

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

        field_list = [field["name"] for field in self.table_fields]
        if sort.lstrip("-") in field_list:
            if sort.startswith("-"):
                print(f"BB-de: {sort}, {sort[1:]}")
                queryset = queryset.order_by(Lower(sort[1:]).desc())
            else:
                print(f"BB-as: {sort}")
                queryset = queryset.order_by(Lower(sort))

        return queryset


class SiteListView(LoginRequiredMixin, SortedListMixin):
    model = Site
    paginate_by = 14
    template_name = "inventory/lists.html"
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "code"

    filter_fields = [
        # {"name": "code", "label": "Code"},
        # This one needs to account for int type, and maybe < or >
        # {"name": "item_count", "label": "Items"},
    ]
    # This gets passed to the template to control display of headers and data:
    # If "sortable" is "no", don't offer sort arrows on the column header.
    # Use "max_chars" to truncate the data to max_chars number of characters.
    table_fields = [
        {"name": "code", "label": "Code"},
        {"name": "name", "label": "Name"},
        {"name": "location", "label": "Location"},
        {"name": "description", "label": "Description", "max_chars": 80},
        {"name": "fieldnotes_count", "label": "No. Fieldnotes"},
        {"name": "equipment_count", "label": "No. Equipment"},
        # {"name": "item_count", "label": "Items"},
    ]

    def get_queryset(self):
        qs = Site.objects.annotate(fieldnotes_count=Count("fieldnotes"))
        qs = qs.annotate(equipment_count=Count("equipment"))
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["reset_url"] = reverse("view_sites")
        context["add_url"] = reverse("site_add")
        context["heading"] = "Sites"
        context["add_button"] = "Add New Site"
        context["edit_url"] = "site_edit"
        context["default_max_chars"] = self._default_max_chars

        return context


class EquipmentListView(LoginRequiredMixin, SortedListMixin):
    model = Equipment
    template_name = "inventory/lists.html"
    paginate_by = 14
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "description"

    filter_fields = [
        # {"name": "description", "label": "Description", "type": "text"},
        # {"name": "serial_number", "label": "Serial number", "type": "text"},
        # {
        #     "name": "location",
        #     "label": "Site",
        #     "type": "text",
        #     "lookup": "location__description",
        # },
        # {"name": "notes", "label": "Notes", "type": "text"},
        # # {"name": "date_purchased_start", "label": "Purchased After", "type": "date", "lookup": "date_purchased", "lookup_type": "gte"},
        # # {"name": "date_purchased_end", "label": "Purchased Before", "type": "date", "lookup": "date_purchased", "lookup_type": "lte"},
        # {
        #     "name": "maintenance_count_min",
        #     "label": "Min Maintenance Records",
        #     "type": "number",
        #     "lookup": "maintenance_count",
        #     "lookup_type": "gte",
        # },
        # # {
        # #     "name": "maintenance_count_max",
        # #     "label": "Max Maintenance Records",
        # #     "type": "number",
        # #     "lookup": "maintenance_count",
        # #     "lookup_type": "lte",
        # # },
    ]
    table_fields = [
        {"name": "instrument", "label": "Instrument"},
        {"name": "serial_number", "label": "Serial number", "sortable": "no"},
        {"name": "location", "label": "Location"},
        {"name": "notes", "label": "Notes", "max_chars": 80, "sortable": "no"},
    ]

    def get_queryset(self):
        qs = Equipment.objects.all()
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["reset_url"] = reverse("view_equipment")
        context["add_url"] = reverse("equipment_add")
        context["heading"] = "Equipment"
        context["add_button"] = "Add Equipment"
        context["edit_url"] = "equipment_edit"
        context["default_max_chars"] = self._default_max_chars

        return context


class FieldNoteListView(LoginRequiredMixin, SortedListMixin):
    model = FieldNote
    paginate_by = 14
    template_name = "inventory/lists.html"
    context_object_name = "table_items"
    # Default sort order
    _sort_key = "date_submitted"
    filter_fields = [
        # See SiteListView for ideas
    ]
    # This gets passed to the template to control display of headers and data:
    # If "sortable" is "no", don't offer sort arrows on the column header.
    # Use "max_chars" to truncate the data to max_chars number of characters.
    table_fields = [
        {"name": "date_submitted", "label": "Date submitted"},
        {"name": "site", "label": "Site"},
        {"name": "display_summary", "label": "Summary"},
        {"name": "submitter", "label": "Submitter"},
    ]

    def get_queryset(self):
        qs = FieldNote.objects.annotate(
            display_summary=Case(
                When(summary__isnull=False, summary__gt="", then="summary"),
                default="note",
                output_field=CharField(),
            )
        )
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["reset_url"] = reverse("view_fieldnotes")
        context["add_url"] = reverse("fieldnote_create")
        context["heading"] = "Field notes"
        context["add_button"] = "Add New Field note"
        context["edit_url"] = "fieldnote_edit"
        context["default_max_chars"] = self._default_max_chars

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


def logout_view(request):
    logout(request)


def test_html(request):
    class User:
        def __init__(self):
            self.is_authenticated = True
            self.username = "HTML Tester"
            self.is_superuser = True

    print("well well, test_html")
    context = {"user": User(), "heading": "Photos"}
    return render(request, "inventory/photos.html", context)
