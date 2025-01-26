# from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return HttpResponse(content=b"Home Page stub")
