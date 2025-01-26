from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    print("boing")
    return HttpResponse(content="Bugger")
