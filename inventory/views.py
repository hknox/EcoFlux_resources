# from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, Http404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    data = {
        "content": "Home Page stub",
    }
    return render(request, "inventory/home.html", data)
