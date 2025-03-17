from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
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
        location = get_object_or_404(Location, id=location_id)

        return location

    def post(self, request, *args, **kwargs):
        print(type(self.get_object()))
        print(self.get_object())
        id = kwargs["pk"]
        print("post", id)
        form = LocationForm(request.POST, request.FILES)
        # form = LocationForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            print(dir(form.instance))
            print(form.instance.id)
            print(dir(form))
            location = form.save()
            return redirect("view_locations")
        else:
            form = LocationForm(request.POST, request.FILES, instance=location)
            data = {
                "form": form,
            }
            return render(request, "inventory/edit_location.html", data)

    def get(self, request, *args, **kwargs):
        id = kwargs["pk"]
        print("get", id)
        if id == 0:
            location = Location.objects.create()
            form = LocationForm()
        else:
            location = self.get_location_object(id)
            form = LocationForm(instance=location)
        data = {
            "form": form,
        }
        return render(request, "inventory/edit_location.html", data)


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
