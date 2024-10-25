from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import csv

from .models import *


def index(request):
    context = {
        'segment': 'dashboard',
    }
    return render(request, "cellviews/index.html", context)


def input_data(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    file = request.FILES["inputData"]
    data = []
    
    header = file.readline()
    header = header.decode("ascii").strip().split(",")
    while line := file.readline():  # iterates through a while loop, as a for loop restarts the position to 0 on in memory file.
        line = line.decode("ascii")
        well, site, cell, *substances = line.strip().split(",")
        data.append((well, site, cell, *substances))
    
    context = {
        "header": header,
        "data": data
    }
    return render(request, "cellviews/components/data_summary_table.html", context)
