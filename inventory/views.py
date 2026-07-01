from datetime import date as date_type
import logging
import os
from pprint import pprint

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Case, CharField, Count, F, Value, When
from django.db.models.functions import Concat, Lower
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from inventory.models import Document, DOI, Equipment, FieldNote, History, Photo, Site
from navigation import get_return_url

from .forms import (
    DocumentUploadForm,
    DocumentForm,
    EquipmentForm,
    FieldNoteForm,
    PhotoForm,
    PhotoUploadForm,
    SiteForm,
)

DEFAULT_MAX_CHARS = 50

logger = logging.getLogger("inventory")

# ====== Utility view functions ======


@login_required
@require_http_methods(["GET"])
def tinymce_get_images(request):
    """Return a list of images associated with a specific fieldnote"""
    fieldnote_id = request.GET.get("fieldnote_id")
    if not fieldnote_id:
        return JsonResponse({"error": "fieldnote_id required"}, status=400)

    fieldnote = FieldNote.objects.get(id=fieldnote_id)
    images = []
    for photo in fieldnote.photos.all():
        url = photo.photo.url
        images.append(
            {
                "title": os.path.basename(url),
                "value": url,
            }
        )

    return JsonResponse(images, safe=False)


@login_required
# without this, browsers will not open the filepicker
@xframe_options_sameorigin
def image_picker_dialogue(request):
    """Render the custom image picker dialog"""
    return render(request, "inventory/image_picker_dialogue.html")


# ====== View mixins ======


class BaseContextMixin:
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


class URLsMixin:
    """This class gets the URL of the next page from the session store
    if available or from detault_success_url set by subclasses.
    """

    def get_success_url(self):
        # Filter out current URL so delete's don't cause issues
        history = self.request.session.get("nav_history", [])
        current = self.request.get_full_path()
        # For deletes, also remove the associated edit URL
        edit_url = current.replace("/delete/", "/edit/")
        history = [url for url in history if url not in (current, edit_url)]
        self.request.session["nav_history"] = history

        return get_return_url(self.request, fallback_viewname=self.default_success_url)

    # def get_success_url(self):
    #     return get_return_url(self.request, fallback_viewname=self.default_success_url)

    def get_cancel_url(self):
        return self.get_success_url()


class SiteAssignmentMixin:
    """
    Handles enabling/disabling the 'site' field and ensuring it still
    submits when disabled.
    """

    # This determines whether the site can be changed after the object
    # has been created
    can_edit_site = False

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # self.object is None on Create
        editing = self.object and self.object.pk is not None
        # site_pk is provded when we will be returning to a site
        # detail after the current operation
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


# ====== Equipment views ======


@login_required
@require_http_methods(["POST"])
def history_update(request, history_pk):
    record = get_object_or_404(History, pk=history_pk)
    date = request.POST.get("date", "").strip()
    note = request.POST.get("note", "").strip()
    errors = {}
    if not date:
        errors["date"] = "Date is required."
    if not note:
        errors["note"] = "Note is required."
    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)
    record.date = date
    record.note = note
    record.save()
    logger.info(f"User {request.user} updated history record {history_pk}.")
    return JsonResponse({"ok": True, "id": record.pk})


@login_required
@require_http_methods(["POST"])
def history_add(request, equipment_pk):
    equipment = get_object_or_404(Equipment, pk=equipment_pk)
    date_str = request.POST.get("date", "").strip()
    note = request.POST.get("note", "").strip()
    errors = {}
    if not date_str:
        errors["date"] = "Date is required."
    if not note:
        errors["note"] = "Note is required."
    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    try:
        parsed_date = date_type.fromisoformat(date_str)
    except ValueError:
        return JsonResponse(
            {"ok": False, "errors": {"date": "Enter a valid date."}}, status=400
        )

    history = History.objects.create(item=equipment, date=parsed_date, note=note)
    logger.info(
        f"User {request.user} added history {history.pk} to equipment {history.item}."
    )
    return JsonResponse(
        {
            "ok": True,
            "id": history.pk,
            "date": str(history.date),
            "note": history.note,
            "remove_url": reverse("history_remove", kwargs={"history_pk": history.pk}),
            "update_url": reverse("history_update", kwargs={"history_pk": history.pk}),
        }
    )


@login_required
@require_http_methods(["POST"])
def history_remove(request, history_pk):

    history = get_object_or_404(History, pk=history_pk)
    equipment = history.equipment
    history.delete()
    logger.info(
        f"User {request.user} removed history {history_pk} from equipment {equipment}."
    )
    return JsonResponse({"ok": True})


class EquipmentViewsMixin(URLsMixin, BaseContextMixin, SiteAssignmentMixin):
    model = Equipment
    form_class = EquipmentForm
    default_success_url = reverse_lazy("view_equipment")
    template_name = "inventory/equipment_detail.html"
    can_edit_site = True

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        return context


class EquipmentCreateView(LoginRequiredMixin, EquipmentViewsMixin, CreateView):
    action_text = "New"

    def form_valid(self, form):
        # Store message before redirect
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully created equipment, {self.object.instrument}."
        )
        return response


class EquipmentUpdateView(LoginRequiredMixin, EquipmentViewsMixin, UpdateView):
    action_text = "Edit"
    delete_url = "equipment_delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment = context["object"]

        context["history_records"] = equipment.history.order_by("date")
        context["history_add_url"] = reverse(
            "history_add", kwargs={"equipment_pk": equipment.pk}
        )
        context["documents"] = equipment.documents
        context["document_create_url"] = (
            reverse("document_add") + f"?equipment_pk={equipment.pk}"
        )
        context["content_type"] = "piece of equipment"
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully updated equipment, {self.object.instrument}."
        )

        return response


class EquipmentDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView
):
    model = Equipment
    success_message = "Inventory item %(instrument)s was deleted successfully!"
    default_success_url = reverse_lazy("view_equipment")

    def form_valid(self, form):
        # Store message before redirect
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully deleted equipment, {self.object.instrument}."
        )
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            instrument=self.object.instrument,
        )


# ====== Fieldnote Views ======


class FieldNoteViewsMixin(URLsMixin, BaseContextMixin, SiteAssignmentMixin):
    model = FieldNote
    form_class = FieldNoteForm
    default_success_url = reverse_lazy("view_fieldnotes")
    delete_url = "fieldnote_delete"
    template_name = "inventory/fieldnote_detail.html"
    can_edit_site = False

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        return context


class FieldNoteCreateView(LoginRequiredMixin, FieldNoteViewsMixin, CreateView):

    action_text = "New"
    base_edit_url = "fieldnote_edit"

    def get_success_url(self):
        """Return the URL to go to after successfully creating a
        fieldnote. This enables adding photos without returning to the
        referrer page.
        """
        return reverse(self.base_edit_url, kwargs={"pk": self.object.pk})

        # Store message before redirect
        messages.success(
            self.request,
            "Fieldnote created successfully. You can now add photos and documents.",
        )
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully created fieldnote for site, {self.object.site}."
        )
        return response
    def get_cancel_url(self):
        return get_return_url(self.request, fallback_viewname=self.default_success_url)




class FieldNoteUpdateView(LoginRequiredMixin, FieldNoteViewsMixin, UpdateView):

    action_text = "Edit"

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully updated fieldnote of {self.object.date_visited} for site {self.object.site}."
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fieldnote = context["object"]

        context["photos"] = fieldnote.photos.all()
        context["photo_add_url"] = reverse("photo_add", args=[context["object"].id])
        photo_count = fieldnote.photos.count()
        context["documents"] = fieldnote.documents.all()
        doc_count = fieldnote.documents.count()
        context["document_create_url"] = (
            reverse("document_add") + f"?fieldnote_pk={fieldnote.pk}"
        )
        context["documents"] = fieldnote.documents
        context["content_type"] = "fieldnote"

        return context


class FieldNoteDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView
):
    model = FieldNote
    default_success_url = reverse_lazy("view_fieldnotes")
    success_message = (
        "Field note of %(date)s for site %(site)s was deleted successfully!"
    )

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully deleted fieldnote of {self.object.date_visited} for site {self.object.site}."
        )
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            date=self.object.date_visited,
            site=self.object.site,
        )


# ====== Site Views ======


@login_required
@require_http_methods(["POST"])
def doi_add(request, site_pk):
    site = get_object_or_404(Site, pk=site_pk)
    label = request.POST.get("label", "").strip()
    doi_link = request.POST.get("doi_link", "").strip()
    errors = {}
    if not label:
        errors["label"] = "Label is required."
    if not doi_link:
        errors["doi_link"] = "DOI link is required."
    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    doi = DOI.objects.create(site=site, label=label, doi_link=doi_link)
    logger.info(f"User {request.user} added DOI {doi.pk} to site {site}.")
    return JsonResponse(
        {
            "ok": True,
            "id": doi.pk,
            "label": doi.label,
            "doi_link": doi.doi_link,
            "remove_url": reverse("doi_remove", kwargs={"doi_pk": doi.pk}),
        }
    )


@login_required
@require_http_methods(["POST"])
def doi_remove(request, doi_pk):
    doi = get_object_or_404(DOI, pk=doi_pk)
    site = doi.site
    doi.delete()
    logger.info(f"User {request.user} removed DOI {doi_pk} from site {site}.")
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def doi_update(request, doi_pk):
    doi = get_object_or_404(DOI, pk=doi_pk)
    label = request.POST.get("label", "").strip()
    doi_link = request.POST.get("doi_link", "").strip()
    errors = {}
    if not label:
        errors["label"] = "Label is required."
    if not doi_link:
        errors["doi_link"] = "DOI link is required."
    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)
    doi.label = label
    doi.doi_link = doi_link
    doi.save()
    logger.info(f"User {request.user} updated DOI {doi.pk} on site {doi.site}.")
    return JsonResponse({"ok": True, "id": doi.pk})


class SiteViewsMixin(URLsMixin, BaseContextMixin):
    """Base model for SiteViewCreate, SiteViewUpdate"""

    model = Site
    form_class = SiteForm
    template_name = "inventory/site_detail.html"
    default_success_url = reverse_lazy("view_sites")
    update_url = "site_edit"
    delete_url = "site_delete"

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        return context


class SiteCreateView(LoginRequiredMixin, SiteViewsMixin, CreateView):
    action_text = "New"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_site"] = False
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Site created successfully. You can now add DOI records, equipment, fieldnotes and documents.",
        )
        logger.info(
            f"User {self.request.user} successfully created site, {self.object}."
        )
        return response

    def get_cancel_url(self):
        """Before the site is created, send the user to the main site
        list if they cancel the new site."""

        return reverse("view_sites")

    def get_success_url(self):
        """If the site is successfully created, send the user to the
        Site edit page so they can attach items like fieldnotes,
        documents and photos."""

        return reverse(self.update_url, kwargs={"pk": self.object.pk})


class SiteUpdateView(LoginRequiredMixin, SiteViewsMixin, UpdateView):
    action_text = "Edit"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["existing_site"] = True
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = context["object"]

        context["doi_records"] = site.doi_records.all()
        context["doi_add_url"] = reverse("doi_add", kwargs={"site_pk": site.pk})

        context["fieldnotes"] = self.object.fieldnotes.order_by("date_visited")
        context["equipment"] = self.object.equipment.all()
        context["success_url"] = (
            f"?{SUCCESS_URL}={self.request.get_full_path()}&site_pk={self.object.id}"
        )
        context["fieldnote_create_url"] = (
            reverse("fieldnote_add") + context["success_url"]
        )
        context["equipment_create_url"] = (
            reverse("equipment_add") + context["success_url"]
        )
        context["return_url"] = f"?{SUCCESS_URL}={self.request.get_full_path()}"
        context["document_create_url"] = (
            reverse("document_add") + context["return_url"] + f"&site_pk={site.id}"
        )
        context["documents"] = site.documents
        context["content_type"] = "site"

        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully updated site, {self.object}."
        )
        return response


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

    def form_valid(self, form):
        # Store message before redirect
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully deleted site, {self.object}."
        )
        return response


# ====== Photo Views ======


class PhotoUploadView(LoginRequiredMixin, URLsMixin, FormView):
    template_name = "inventory/photo_upload.html"
    form_class = PhotoUploadForm
    default_success_url = reverse_lazy("view_photos")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        initial = {}
        initial["date_taken"] = self.fieldnote.date_visited
        kwargs["initial"] = initial

        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.fieldnote = get_object_or_404(FieldNote, pk=kwargs["fieldnote"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fieldnote"] = self.fieldnote
        context["cancel_url"] = self.get_success_url()

        return context

    def form_valid(self, form):
        taken_by = form.cleaned_data.get("taken_by", "")
        date_taken = form.cleaned_data["date_taken"]
        photos = form.cleaned_data["photos"]
        num_photos = len(photos)

        for f in photos:
            Photo.objects.create(
                fieldnote=self.fieldnote,
                photo=f,
                taken_by=taken_by,
                date_taken=date_taken,
            )
        logger.info(
            f"User {self.request.user} uploaded {num_photos} photos taken at site {self.fieldnote.site} on {date_taken} by {taken_by}."
        )

        return super().form_valid(form)


class PhotoUpdateView(LoginRequiredMixin, URLsMixin, BaseContextMixin, UpdateView):

    action_text = "Edit"
    model = Photo
    form_class = PhotoForm
    template_name = "inventory/photo_detail.html"
    default_success_url = reverse_lazy("view_photos")
    delete_url = "photo_delete"

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully updated a photo taken at {self.object.fieldnote.site} on {self.object.date_taken} by {self.object.taken_by}."
        )

        return response

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)
        context["record_type"] = "Photo"

        return context


class PhotoDeleteView(LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView):
    model = Photo
    default_success_url = reverse_lazy("view_photos")
    success_message = "Photo of %(date)s for site %(site)s was deleted successfully!"

    def form_valid(self, form):
        response = super().form_valid(form)
        # delete the associated image file
        self.object.photo.delete(save=False)
        self.object.thumbnail.delete(save=False)
        logger.info(
            f"User {self.request.user} successfully deleted a photo taken at {self.object.fieldnote.site} on {self.object.date_taken} by {self.object.taken_by}."
        )
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            date=(
                self.object.date_taken
                if self.object.date_taken
                else self.object.fieldnote.date_visited
            ),
            site=self.object.fieldnote.site,
        )


# ====== Document Views ======


class DocumentUploadView(LoginRequiredMixin, URLsMixin, FormView):
    template_name = "inventory/document_upload.html"
    form_class = DocumentUploadForm
    default_success_url = reverse_lazy("view_documents")

    content_type_map = {"equipment": Equipment, "fieldnote": FieldNote, "site": Site}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # initial from super.get_form_arguments() will be empty.
        initial = {}
        initial["date_uploaded"] = f"{date_type.today()}"
        user = self.request.user
        name = f"{user.first_name} {user.last_name}"
        username = name if name.strip() else user.username.capitalize()
        initial["submitter"] = username
        kwargs["initial"] = initial

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()

        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        # Sort out the generic foreign key for this document: site_pk,
        # equipment_pk or fieldnote_id are provded as part of the
        # request path when we want to upload a document from a site,
        # equipment or fieldnote view. Here we want to determine which
        # data type and object id will be associated with this
        # document.
        # We do this here since they depend on request context.
        for content in ["equipment", "fieldnote", "site"]:
            object_id = self.request.GET.get(f"{content}_pk")
            if object_id:
                obj.content_type = ContentType.objects.get_for_model(
                    self.content_type_map[content]
                )
                obj.object_id = object_id
                break
        else:
            raise TypeError(
                f"Requested an unknown relationship for a document: {self.request.get_full_path()}"
            )
        obj.save()
        logger.info(
            f"User {self.request.user} uploaded a document received on {obj.date_received} ({obj.summary})."
        )

        return super().form_valid(form)


class DocumentUpdateView(LoginRequiredMixin, URLsMixin, BaseContextMixin, UpdateView):

    action_text = "Edit"
    model = Document
    form_class = DocumentForm
    template_name = "inventory/document_detail.html"
    default_success_url = reverse_lazy("view_documents")
    delete_url = "document_delete"

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            f"User {self.request.user} successfully updated a document received on {self.object.date_received}: {self.object.summary}."
        )
        return response

    def get_context_data(self, **kwargs):
        context = self.get_base_context_data(**kwargs)

        return context


class DocumentDeleteView(
    LoginRequiredMixin, SuccessMessageMixin, URLsMixin, DeleteView
):
    model = Document
    default_success_url = reverse_lazy("view_documents")
    success_message = "Document of %(date)s (%(summary)s) was deleted successfully!"

    def form_valid(self, form):
        response = super().form_valid(form)
        # delete the associated file
        self.object.file.delete(save=False)
        self.object.thumbnail.delete(save=False)
        logger.info(
            f"User {self.request.user} successfully deleted a document received on {self.object.date_received}: {self.object.summary}."
        )
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(
            cleaned_data,
            date=self.object.date_received,
            summary=self.object.summary,
        )


# ====== List Mixins ======


class SortedListMixin(ListView):
    """Add persistent sort machinery to ListView.

    Pass a table_fields list of dicts for the template via the context
    to control display of headers and data, eg:

    table_fields = [
        {"name": "date_visited", "label": "Date visitied", "max_chars": DEFAULT_MAX_CHARS, "sortable": "yes"},
        {"name": "site", "label": "Site", "max_chars": DEFAULT_MAX_CHARS, "sortable": "no"},
        {"name": "display_summary", "label": "Summary", "max_chars": DEFAULT_MAX_CHARS, "sortable": "no"},
    ]

    use these keys for more control:
    - "sortable": if "no", don't offer sort arrows on the column header.
    - "max_chars": truncate the data to max_chars number of characters.
    """

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

        field_list = [field["name"] for field in self.table_fields]
        if sort.lstrip("-") in field_list:
            sort_field = sort.lstrip("-")
            is_descending = sort.startswith("-")

        # Check if this is an annotation
        if sort_field in queryset.query.annotations:
            # For annotations like Count, don't use Lower() — sort by numeric value
            if is_descending:
                queryset = queryset.order_by(F(sort_field).desc())
            else:
                queryset = queryset.order_by(sort_field)
        else:
            # For regular fields, use Lower() for case-insensitive sorting
            if is_descending:
                queryset = queryset.order_by(Lower(sort_field).desc())
            else:
                queryset = queryset.order_by(Lower(sort_field))

        return queryset


# ====== List Views ======


class SiteListView(LoginRequiredMixin, SortedListMixin):
    model = Site
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
        {
            "name": "code",
            "label": "Code",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "name",
            "label": "Name",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "description",
            "label": "Description",
            "max_chars": 80,
            "sortable": "yes",
        },
        {
            "name": "gps_coordinates",
            "label": "GPS",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "dates_active",
            "label": "Active",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "fieldnotes_count",
            "label": "Notes",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "equipment_count",
            "label": "Eqt",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {"name": "photo_count", "label": "Photos", "sortable": ""},
    ]

    def get_queryset(self):
        # See https://docs.djangoproject.com/en/6.0/topics/db/aggregation/,
        # "Combining multiple aggregations" for caveats re annotate().
        qs = Site.objects.annotate(
            fieldnotes_count=Count("fieldnotes", distinct=True),
            equipment_count=Count("equipment", distinct=True),
            photo_count=Count("fieldnotes__photos", distinct=True),
            dates_active=Concat(
                F("date_activated"),
                Value(" - "),
                Case(
                    When(date_retired__isnull=False, then=F("date_retired")),
                    default=Value("[ongoing]"),
                    output_field=CharField(),
                ),
                output_field=CharField(),
            ),
        )
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["heading"] = "Sites"
        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["add_button"] = "Add New Site"
        context["add_url"] = reverse("site_add")
        context["edit_url"] = "site_edit"
        # This will only be used when filtering is re-implemented.
        context["reset_url"] = reverse("view_sites")

        return context


class EquipmentListView(LoginRequiredMixin, SortedListMixin):
    model = Equipment
    template_name = "inventory/lists.html"
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
        {
            "name": "instrument",
            "label": "Instrument",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "serial_number",
            "label": "Serial number",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "no",
        },
        {
            "name": "site",
            "label": "Location",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {"name": "notes", "label": "Notes", "max_chars": 80, "sortable": "no"},
        # {
        #     "name": "history_count",
        #     "label": "# History records",
        #     "max_chars": DEFAULT_MAX_CHARS,
        #     "sortable": "no",
        # },
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

        return context


class FieldNoteListView(LoginRequiredMixin, SortedListMixin):
    model = FieldNote
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
        {
            "name": "date_visited",
            "label": "Date visited",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "site",
            "label": "Site",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "display_summary",
            "label": "Summary",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "submitter",
            "label": "Submitter",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "photo_count",
            "label": "# Photos",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
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
        context["add_button"] = "Add Field note"
        context["edit_url"] = "fieldnote_edit"

        return context


class PhotoListView(LoginRequiredMixin, ListView):
    model = Site
    template_name = "inventory/photo_list.html"
    context_object_name = "sites"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_queryset(self):
        return Site.objects.prefetch_related("fieldnotes__photos").order_by(
            "name"
        )  # optional, for consistency


class DocumentListView(LoginRequiredMixin, SortedListMixin):
    model = Document
    template_name = "inventory/lists.html"
    context_object_name = "table_items"
    _sort_key = "date_received"  # default sort key

    filter_fields = [
        # {"name": "code", "label": "Code"},
        # This one needs to account for int type, and maybe < or >
        # {"name": "item_count", "label": "Items"},
    ]
    # This gets passed to the template to control display of headers and data:
    # If "sortable" is "no", don't offer sort arrows on the column header.
    # Use "max_chars" to truncate the data to max_chars number of characters.
    table_fields = [
        {
            "name": "date_received",
            "label": "Date Received",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "summary",
            "label": "Summary",
            "max_chars": DEFAULT_MAX_CHARS,
            "sortable": "yes",
        },
        {
            "name": "object_description",
            "href": "context_object_url",
            "label": "Related to",
            "max_chars": 80,
            "sortable": "yes",
        },
    ]

    def get_queryset(self):
        qs = Document.objects.prefetch_related("content_type")
        qs = self.apply_filters(qs)
        qs = self.apply_sort_parameters(qs)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["sort"] = self._sort_key
        context["filter_fields"] = self.filter_fields
        context["table_fields"] = self.table_fields
        context["reset_url"] = reverse("view_documents")
        context["heading"] = "Document Library"
        context["edit_url"] = "document_edit"

        return context


def logout_view(request):
    logout(request)
