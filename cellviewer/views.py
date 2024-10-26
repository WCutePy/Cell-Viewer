import polars as pl
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
    data = pl.read_csv(file)
    
    header = data.columns

    context = {
            "header": header,
            "data": data.head(8).rows()
        }

    return render(request, "cellviews/components/data_summary_table.html", context)
