from django.db.models import Case, When, CharField, Count, F, Value
from django.db.models.functions import Lower, Concat
from django.views.generic.list import ListView
from django.views.generic.edit import (
    UpdateView,
    CreateView,
    DeleteView,
    FormView,
)
from django.views.generic import TemplateView
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse

# from django.http import JsonResponse

from pprint import pprint

from inventory.models import Site, FieldNote, Equipment, Photo
from .forms import (
    HistoryFormSet,
    PhotoUploadForm,
    SiteForm,
    DOIFormSet,
    FieldNoteForm,
    EquipmentForm,
    PhotoForm,
)


# This URL parameter tells us where to go after creating or editing an
# inventory item.
SUCCESS_URL = "home"


# ====== View mixins ======


class URLsMixin:
    """This class provide several ways to get the URL of the next
    page, either from a URL parameter if provided or from
    detault_success_url set by subclasses.

    """

    def get_success_url(self):
        return self.request.GET.get(SUCCESS_URL, self.default_success_url)

    # CreateViews override get_success_url() which get_context_data()
    # uses to get the URL for the cancel button during item creation.
    # CreateVew.get_success_url() will fail during item creation
    # because the created object doesn't yet exist in the database.
    get_cancel_url = get_success_url

    def get_create_success_url(self, edit_url):
        """FieldnoteCreateView uses this after a fieldnote has been
        created to enable adding photos without returning to the
        referrer page."""
        edit_url = reverse(edit_url, kwargs={"pk": self.object.pk})
        # Save return urls until we've finished editing the new fieldnote.
        next_url = self.request.GET.get(SUCCESS_URL, "")
        next_url = f"?{SUCCESS_URL}={next_url}" if next_url else ""
        return edit_url + next_url


class ContextMixin:
    """This class sets up the base context dict for Create, Update and
    Delete views."""

    def get_base_context_data(self, **kwargs):
        # super().keys(): 'object', 'form', 'view', 'model' (eg 'fieldnote')
        context = super().get_context_data(**kwargs)
        context["action"] = self.action_text
        if isinstance(self, CreateView):
            context["cancel_url"] = self.get_cancel_url()
        if isinstance(self, UpdateView):
            context["delete_url"] = reverse(
                self.delete_url,
                args=[
                    context["object"].id,
                ],
            )

            context["default_success_url"] = self.default_success_url
            context["success_param"] = SUCCESS_URL
        return context


class SiteAssignmentMixin:
    """
    Handles enabling/disabling the 'site' field and ensuring it still
    submits when disabled.
    """

    # This determines whether the site can be changed after the object
    # has been created
    can_edit_site = False

    # def get_initial(self):
    #     initial = super().get_initial()
    #     site_pk = self.request.GET.get("site_pk")
    #     if site_pk:
    #         initial["site"] = site_pk
    #     return initial

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        site = self.request.GET.get("site_pk")
        if site:
            kwargs["site_id"] = site

        return kwargs

    def enable_site_editing(self):
        """
        Override in subclasses:
        - Equipment: return True for editing
        - Others: return False for editing
        """
        return self.can_edit_site


class FormsetMixin:
    """Mixin to manage issues around formsets.

    The form_valid() method is part of Django’s generic class-based
    view workflow. If you override post() and handle all form and
    formset logic there (including saving and redirecting), Django
    will not call form_valid. Your logic in post() takes precedence.

    When would you need form_valid? If you rely on the default CBV
    flow (don’t override post()), you would only need to override
    form_valid to add formset-handling logic after the parent form is
    saved.

    """

    def get_formset_context_data(self):
        """Return a dict of formset context data."""

        context = {}

        # Use cached versions if present (from POST)
        context["form"] = getattr(self, "_form", self.get_form())
        # Handle formset safely across Create and Update
        if hasattr(self, "_formset"):
            context[self.formset_key] = self._formset
        elif hasattr(self, "object") and self.object is not None:
            context[self.formset_key] = self.formset_class(instance=self.object)
        else:
            context[self.formset_key] = self.formset_class()

        return context

    def post(self, request, *args, **kwargs):
        if isinstance(self, CreateView):
            self.object = None  # required for CreateView
        else:
            self.object = self.get_object()

        # Construct form and formset here
        form = self.get_form()
        formset = (
            self.formset_class(request.POST)
            if self.object is None
            else self.formset_class(request.POST, instance=self.object)
        )

        # Store for use in get_context_data()
        self._form = form
        self._formset = formset

        if form.is_valid() and formset.is_valid():
            return self.form_and_formset_valid(form, formset)
        else:
            return self.render_to_response(self.get_context_data())

    def form_and_formset_valid(self, form, formset):
        model_instance = form.save()
        formset.instance = model_instance
        formset.save()
        self.object = model_instance
        return redirect(self.get_success_url())


class UnderConstructionMixin:
    """
    Mixin to override dispatch and always render an under-construction page.
    Useful for temporarily disabling views during development.
    """

    under_construction_template = "inventory/under_construction.html"
    under_construction_message = (
        "This page is still being built. Please check back another time!"
    )

    def dispatch(self, request, *args, **kwargs):
        return TemplateView.as_view(
            template_name=self.under_construction_template,
            extra_context={"message": self.under_construction_message},
        )(request, *args, **kwargs)


# ====== Equipment views ======


class EquipmentViewsMixin(URLsMixin, ContextMixin, FormsetMixin, SiteAssignmentMixin):
    model = Equipment
    form_class = EquipmentForm
    formset_class = HistoryFormSet
    formset_key = "history_formset"
    default_success_url = reverse_lazy("view_equipment")
    template_name = "inventory/equipment_detail.html"
    can_edit_site = True

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        context.update(self.get_formset_context_data())
        return context


class EquipmentCreateView(LoginRequiredMixin, EquipmentViewsMixin, CreateView):

    action_text = "New"

    def form_valid(self, form):
        # Store message before redirect
        messages.success(
            self.request,
            "Equipment item created successfully. You can now add photos.",
        )
        response = super().form_valid(form)
        return response


class EquipmentUpdateView(LoginRequiredMixin, EquipmentViewsMixin, UpdateView):

    action_text = "Edit"
    delete_url = "equipment_delete"


class EquipmentDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView
):
    model = Equipment
    success_message = "Inventory item %(instrument)s was deleted successfully!"
    default_success_url = reverse_lazy("view_equipment")

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            instrument=self.object.instrument,
        )


# ====== Fieldnote Views ======


class FieldNoteViewsMixin(URLsMixin, ContextMixin, SiteAssignmentMixin):
    model = FieldNote
    form_class = FieldNoteForm
    default_success_url = reverse_lazy("view_fieldnotes")
    delete_url = "fieldnote_delete"
    template_name = "inventory/fieldnote_detail.html"
    can_edit_site = False

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        if isinstance(self, UpdateView):
            context["photos"] = self.object.photos.all()
            context["success_url"] = f"?{SUCCESS_URL}={self.request.get_full_path()}"
            context["photo_add_url"] = (
                reverse("photo_add", args=[context["object"].id])
                + context["success_url"]
            )
        return context


class FieldNoteCreateView(LoginRequiredMixin, FieldNoteViewsMixin, CreateView):

    action_text = "New"

    def get_success_url(self):
        return self.get_create_success_url("fieldnote_edit")

    def form_valid(self, form):
        # Store message before redirect
        messages.success(
            self.request,
            "Fieldnote created successfully. You can now add photos.",
        )
        response = super().form_valid(form)
        return response


class FieldNoteUpdateView(LoginRequiredMixin, FieldNoteViewsMixin, UpdateView):

    action_text = "Edit"


class FieldNoteDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView
):
    model = FieldNote
    default_success_url = reverse_lazy("view_fieldnotes")
    success_message = (
        "Field note of %(date)s for site %(site)s was deleted successfully!"
    )

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            date=self.object.date_visited,
            site=self.object.site,
        )


# ====== Site Views ======


class SiteViewsMixin(URLsMixin, ContextMixin, FormsetMixin):
    """Base model for SiteViewCreate, SiteViewUpdate"""

    model = Site
    form_class = SiteForm
    formset_class = DOIFormSet
    formset_key = "doi_formset"
    template_name = "inventory/site_detail.html"
    default_success_url = reverse_lazy("view_sites")
    update_url_name = "site_edit"
    delete_url = "site_delete"

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        context.update(self.get_formset_context_data())
        return context


class SiteCreateView(LoginRequiredMixin, SiteViewsMixin, CreateView):
    action_text = "New"

    def form_valid(self, form, formset):
        response = super().form_valid(form, formset)
        # Store message before redirect
        messages.success(
            self.request,
            "Site created successfully. You can now add equipment and fieldnotes.",
        )
        return response

    def get_success_url(self):
        return reverse(self.update_url_name, kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_site"] = False
        return kwargs


class SiteUpdateView(LoginRequiredMixin, SiteViewsMixin, UpdateView):

    action_text = "Edit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fieldnotes"] = self.object.fieldnotes.order_by("date_visited")
        context["equipment"] = self.object.equipment.all()
        # Add context for accordions in templates
        # SUCCESS_URL serves to set page to return to after editing/deleting
        context["success_url"] = (
            f"?{SUCCESS_URL}={self.request.get_full_path()}&site_pk={self.object.id}"
        )
        context["fieldnote_create_url"] = (
            reverse("fieldnote_add") + context["success_url"]
        )
        context["equipment_create_url"] = (
            reverse("equipment_add") + context["success_url"]
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_site"] = True
        return kwargs


class SiteDeleteView(LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView):
    model = Site
    default_success_url = reverse_lazy("view_sites")
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


# ====== Photo Views ======


class PhotoUploadView(LoginRequiredMixin, URLsMixin, FormView):
    template_name = "inventory/photo_upload.html"
    form_class = PhotoUploadForm
    default_success_url = reverse_lazy("view_fieldnotes")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        date_taken = self.fieldnote.date_visited
        kwargs["initial_date"] = date_taken
        print("photo upload kwargs")
        pprint(kwargs)
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.fieldnote = get_object_or_404(FieldNote, pk=kwargs["fieldnote"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print("PhotoUploadView.get_context_data()")
        context = super().get_context_data(**kwargs)
        context["fieldnote"] = self.fieldnote
        context["cancel_url"] = self.get_success_url()

        return context

    def form_valid(self, form):
        print("PhotoUploadView.form_valid()")
        taken_by = form.cleaned_data.get("taken_by", "")
        print(f"taken by: {taken_by}")
        print("cleaned form:", form.cleaned_data)
        photos = form.cleaned_data["photos"]
        date_taken = form.cleaned_data["date_taken"]
        print(f"photos: {photos}")
        for f in photos:
            Photo.objects.create(
                fieldnote=self.fieldnote,
                photo=f,
                taken_by=taken_by,
                date_taken=date_taken,
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form invalid called")
        print("FILES:", self.request.FILES)
        print("POST:", self.request.POST)
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class PhotoUpdateView(LoginRequiredMixin, URLsMixin, ContextMixin, UpdateView):

    action_text = "Edit"
    model = Photo
    form_class = PhotoForm
    template_name = "inventory/photo_detail.html"
    default_success_url = reverse_lazy("view_photos")
    delete_url = "photo_delete"

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        # # Add context for accordions in templates
        # # SUCCESS_URL serves to set page to return to after editing/deleting
        # context["success_url"] = (
        #     f"?{SUCCESS_URL}={self.request.get_full_path()}&site_pk={self.object.id}"
        # )
        # context["fieldnote_create_url"] = (
        #     reverse("fieldnote_add") + context["success_url"]
        # )
        # context["equipment_create_url"] = (
        #     reverse("equipment_add") + context["success_url"]
        # )
        pprint(context)
        return context


class PhotoDeleteView(LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView):
    model = Photo
    default_success_url = reverse_lazy("view_photos")
    success_message = "Photo of %(date)s for site %(site)s was deleted successfully!"

    def get_success_message(self, cleaned_data):
        pprint(
            dict(
                cleaned_data,
                date=(
                    self.object.date_taken
                    if self.object.date_taken
                    else self.object.fieldnote.date_visited
                ),
                site=self.object.fieldnote.site,
            )
        )
        return self.success_message % dict(
            cleaned_data,
            date=(
                self.object.date_taken
                if self.object.date_taken
                else self.object.fieldnote.date_visited
            ),
            site=self.object.fieldnote.site,
        )


# ====== List Mixins ======


class SortedListMixin(ListView):
    """Add persistent sort machinery to ListView.

    Pass a table_fields list of dicts for the template via the context
    to control display of headers and data, eg:

    table_fields = [
        {"name": "date_visited", "label": "Date visitied"},
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


# ====== List Views ======


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
        {"name": "description", "label": "Description", "max_chars": 60},
        {"name": "gps_coordinates", "label": "GPS"},
        {"name": "dates_active", "label": "Active"},
        {"name": "fieldnotes_count", "label": "Notes", "sortable": ""},
        {"name": "equipment_count", "label": "Eqt", "sortable": ""},
        # {"name": "photo_count", "label": "Photos", "sortable": ""},
    ]

    def get_queryset(self):
        # See https://docs.djangoproject.com/en/5.2/topics/db/aggregation/,
        # "Combining multiple aggregations" for caveats re annotate().
        qs = Site.objects.annotate(
            fieldnotes_count=Count("fieldnotes", distinct=True),
            equipment_count=Count("equipment", distinct=True),
            # photo_count=Count("photos", distinct=True),
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
        context["add_url"] = (
            reverse("site_add") + f"?{SUCCESS_URL}={reverse('view_sites')}"
        )
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
    _sort_key = "instrument"

    filter_fields = [
        # {"name": "instrument", "label": "Instrument", "type": "text"},
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
        {"name": "site", "label": "Location"},
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
    _sort_key = "date_visited"
    filter_fields = [
        # See SiteListView for ideas
    ]
    # This gets passed to the template to control display of headers and data:
    # If "sortable" is "no", don't offer sort arrows on the column header.
    # Use "max_chars" to truncate the data to max_chars number of characters.
    table_fields = [
        {"name": "date_visited", "label": "Date visited"},
        {"name": "site", "label": "Site"},
        {"name": "display_summary", "label": "Summary"},
        {"name": "submitter", "label": "Submitter"},
        {"name": "photo_count", "label": "# Photos"},
    ]

    def get_queryset(self):
        qs = FieldNote.objects.annotate(
            display_summary=Case(
                When(summary__isnull=False, summary__gt="", then="summary"),
                default="note",
                output_field=CharField(),
            )
        ).annotate(photo_count=Count("photos"))
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["reset_url"] = reverse("view_fieldnotes")
        context["add_url"] = reverse("fieldnote_add")
        context["heading"] = "Field notes"
        context["add_button"] = "Add New Field note"
        context["edit_url"] = "fieldnote_edit"
        context["default_max_chars"] = self._default_max_chars

        return context


class PhotoListView(UnderConstructionMixin, ListView):
    under_construction_message = (
        "This photo listing page is still being built. Please check back another time!"
    )


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
