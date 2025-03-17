from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from inventory.models import Location


class LocationDeleteView(LoginRequiredMixin, DeleteView):
    model = Location
    fields = ["description", "address", "gps_coordinates"]
    template_name_suffix = "_delete_form"
    success_url = reverse_lazy("view_locations")


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


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    paginate_by = 14
    template_name = "inventory/location_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to context as needed...
        return context


@login_required
def home(request):
    data = {
        "content": "Home Page stub",
    }
    return render(request, "inventory/home.html", data)
