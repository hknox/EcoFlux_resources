# from django.contrib.auth.forms import password_validation
from django.db.models import Case, When, CharField, Count, F, Value
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import redirect, render  # get_object_or_404

# from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.functions import Lower, Concat
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse


from inventory.models import Site, FieldNote, Equipment
from .forms import (
    HistoryFormSet,
    SiteForm,
    DOIFormSet,
    FieldNoteForm,
    EquipmentForm,
)


def EndOfInternet(request):
    return redirect("https://hmpg.net/")


class AjaxFormMixin:
    """We keep our normal `CreateView`/`UpdateView`, but make them
    detect AJAX and return only the form HTML.
    """

    ajax_template_name = None  # set in subclass

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render(
                self.request, self.ajax_template_name, {"form": form}
            ).content.decode("utf-8")
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)

    def form_valid(self, form):
        obj = form.save()
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            # Render the updated row or list
            row_html = render(
                self.request, self.row_template_name, {"object": obj}
            ).content.decode("utf-8")
            return JsonResponse(
                {"success": True, "row_html": row_html, "object_id": obj.pk}
            )
        return super().form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            self.object = None if isinstance(self, CreateView) else self.get_object()
            form = self.get_form()
            html = render(
                request, self.ajax_template_name, {"form": form}
            ).content.decode("utf-8")
            print(JsonResponse({"html": html}).text)
            return JsonResponse({"html": html})
        return super().get(request, *args, **kwargs)


class SiteAssignmentMixin:
    """
    Handles enabling/disabling the `site` field and ensuring it still
    submits when disabled.
    """

    def get_initial(self):
        initial = super().get_initial()
        site_pk = self.request.GET.get("site_pk")
        if site_pk:
            initial["site"] = site_pk
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # self.object is None on Create
        editing = self.object and self.object.pk is not None
        site_pk = self.request.GET.get("site_pk")

        # Logic for enabling/disabling
        if (site_pk or editing) and not self.enable_site_editing():
            form.fields["site"].disabled = True
            form.fields["site"].widget.attrs["data-locked"] = "true"
            form.fields["site"].widget.attrs["data-site-id"] = site_pk
        return form

    def enable_site_editing(self):
        """
        Override in subclasses:
        - Equipment: return True for editing
        - Others: return False for editing
        """
        return False


class EquipmentViewsMixin(SiteAssignmentMixin):
    model = Equipment
    form_class = EquipmentForm
    template_name = "inventory/equipment_detail.html"
    ajax_template_name = "inventory/equipment_ajax_form.html"
    row_template_name = "inventory/equipment_row.html"

    def form_valid(self, form):
        form.instance.site_id = self.kwargs["site_pk"]
        return super().form_valid(form)

    def initialize_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        context["cancel_url"] = self.request.GET.get(
            "next", reverse_lazy("view_equipment")
        )

        # Use cached versions if present (from POST)
        context["form"] = getattr(self, "_form", self.get_form())
        # Handle formset safely across Create and Update
        if hasattr(self, "_formset"):
            context["history_formset"] = self._formset
        elif hasattr(self, "object") and self.object is not None:
            context["history_formset"] = HistoryFormSet(instance=self.object)
        else:
            context["history_formset"] = HistoryFormSet()

        return context

    def post(self, request, *args, **kwargs):
        if isinstance(self, CreateView):
            self.object = None  # required for CreateView
        else:
            self.object = self.get_object()

        # Construct form and formset here
        form = self.get_form()
        if not self.object:
            # New site
            formset = HistoryFormSet(request.POST)
        else:
            # Existing site
            formset = HistoryFormSet(request.POST, instance=self.object)

        # Store for use in get_context_data()
        self._form = form
        self._formset = formset

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        #     site = form.save()
        #     formset.instance = site
        #     formset.save()
        #     return redirect(self.get_success_url())

        # return self.render_to_response(self.get_context_data())

    def enable_site_editing(self, editing):
        return True  # Equipment can change site when editing

    def get_success_url(self):
        # "next" can be set in the template of a page you want to return to:
        return self.request.GET.get("next", reverse_lazy("view_equipment"))


class EquipmentCreateView(LoginRequiredMixin, EquipmentViewsMixin, CreateView):

    action = "New"

    def get_context_data(self, **kwargs):
        return self.initialize_context_data(**kwargs)


class EquipmentUpdateView(LoginRequiredMixin, EquipmentViewsMixin, UpdateView):

    action = "Edit"

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = self.action
        context["delete_url"] = reverse(
            "site_delete",
            args=[
                context["object"].id,
            ],
        )
        context["form"] = getattr(self, "_form", self.get_form())
        context["history_formset"] = getattr(
            self, "_formset", HistoryFormSet(instance=self.get_object())
        )
        return context


class FieldNoteViewsMixin(SiteAssignmentMixin):
    model = FieldNote
    form_class = FieldNoteForm
    template_name = "inventory/fieldnote.html"

    def initialize_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.request.GET.get(
            "next", reverse_lazy("view_fieldnotes")
        )
        return context

    def enable_site_editing(self):
        return False  # Keep disabled, but can change later if needed

    def get_success_url(self):
        return self.request.GET.get("next", reverse_lazy("view_fieldnotes"))


class FieldNoteCreateView(LoginRequiredMixin, FieldNoteViewsMixin, CreateView):

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["site_id"] = self.request.GET.get("site")

        return kwargs


class FieldNoteUpdateView(LoginRequiredMixin, FieldNoteViewsMixin, UpdateView):

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data()
        context["delete_url"] = reverse(
            "fieldnote_delete",
            args=[
                context["object"].id,
            ],
        )
        return context


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

        # Use cached versions if present (from POST)
        context["form"] = getattr(self, "_form", self.get_form())
        # Handle formset safely across Create and Update
        if hasattr(self, "_formset"):
            context["doi_formset"] = self._formset
        elif hasattr(self, "object") and self.object is not None:
            context["doi_formset"] = DOIFormSet(instance=self.object)
        else:
            context["doi_formset"] = DOIFormSet()

        return context

    def post(self, request, *args, **kwargs):
        # Construct form and formset here
        if isinstance(self, CreateView):
            self.object = None  # required for CreateView
        else:
            self.object = self.get_object()

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

    action = "New"

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = self.action
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_site"] = False
        return kwargs


class SiteUpdateView(LoginRequiredMixin, SiteViewsMixin, UpdateView):

    action = "Edit"

    def get_context_data(self, **kwargs):
        context = self.initialize_context_data(**kwargs)
        context["action"] = self.action
        context["delete_url"] = reverse(
            "site_delete",
            args=[
                context["object"].id,
            ],
        )
        context["fieldnotes"] = self.object.fieldnotes.order_by("date_submitted")
        context["equipment"] = self.object.equipment.all()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
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

    use extra keys for more control:
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
        {"name": "description", "label": "Description", "max_chars": 80},
        {"name": "gps_coordinates", "label": "GPS"},
        {"name": "dates_active", "label": "Active"},
        {"name": "fieldnotes_count", "label": "# Fieldnotes"},
        {"name": "equipment_count", "label": "# Equipment"},
    ]

    def get_queryset(self):
        # See https://docs.djangoproject.com/en/5.2/topics/db/aggregation/,
        # "Combining multiple aggregations" for caveaats re annotate().
        qs = Site.objects.annotate(
            fieldnotes_count=Count("fieldnotes", distinct=True),
            equipment_count=Count("equipment", distinct=True),
            dates_active=Concat(
                F("date_activated"),
                Value(" - "),
                (F("date_retired") if F("date_retired") == "" else Value("[ongoing]")),
                output_field=CharField(),
            ),
        )
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
        {"name": "history_count", "label": "# History records", "sortable": "no"},
    ]

    def get_queryset(self):
        qs = Equipment.objects.all()
        qs = qs.annotate(history_count=Count("history"))

        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["heading"] = "Equipment"
        context["table_fields"] = self.table_fields
        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["add_button"] = "Add Equipment"
        context["add_url"] = reverse("equipment_add")
        context["edit_url"] = "equipment_edit"
        context["reset_url"] = reverse("view_equipment")
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
