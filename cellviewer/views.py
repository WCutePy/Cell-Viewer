import base64
import json

import pandas as pd
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
    
    request.session["celldash_df_data"] = file.open().read().decode("utf-8")
    
    request.session.modified = True

    context = {
            "header": header,
            "table_data": data.head(8).rows(),
            # "hists": json.dumps(hists),
            # "hist_amount": range(len(hists)),
        }

    return render(request, "cellviews/components/post_upload_page_part.html", context)
