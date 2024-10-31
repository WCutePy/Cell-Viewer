import json

import polars as pl
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import csv

from .util import plots


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
    
    hists = plots.create_all_hist_html(data, header[3:])

    context = {
            "header": header,
            "table_data": data.head(8).rows(),
            "hists": json.dumps(hists),
            "hist_amount": range(len(hists)),
        }

    return render(request, "cellviews/components/post_upload_page_part.html", context)
