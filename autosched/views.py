from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login

# Create your views here.
def home(request):
    return render(request, "autosched/index.html")

def login(request):
    return render(request, "autosched/login.html")

def dashboard(request):
    return render(request, "autosched/dashboard.html")

def generate(request):
    return render(request, "autosched/generate.html")