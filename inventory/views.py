from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from inventory.forms import LocationForm
from inventory.models import Location


class LocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    form = LocationForm
    template_name = "inventory/edit_location.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def get_location_object(self, location_id):
        if location_id == 0:
            # New location
            location = Location.objects.create()
        else:
            # Existing location
            location = get_object_or_404(Location, id=location_id)

        return location

    def post(self, request, *args, **kwargs):
        id = kwargs["pk"]
        location = self.get_location_object(id)
        form = LocationForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            location = form.save()
            return redirect("view_locations")
        else:
            data = {
                "form": form,
            }
            return render(request, "inventory/edit_location.html", data)

    def get(self, request, *args, **kwargs):
        id = kwargs["pk"]
        location = self.get_location_object(id)
        if id == 0:
            form = LocationForm()
        else:
            form = LocationForm(instance=location)

        data = {
            "form": form,
        }
        return render(request, "inventory/edit_location.html", data)


# @method_decorator(login_required, "dispatch")
class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    paginate_by = 25
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
