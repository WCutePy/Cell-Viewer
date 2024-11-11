import polars as pl
from django.shortcuts import render
from cellviewer.models import SavedJob


def index(request):
    context = {
        'segment': 'index',
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
        "table_data": data.head(5).rows(),
    }
    
    return render(request, "cellviews/components/save_and_request_dash_app.html", context)


def dash_or_save(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    file = request.FILES["inputData"]
    
    print(request.POST.get("submit"))
    if request.POST.get("submit") == "save":
        SavedJob.objects.create(
            request,
            file
        )
        return
    elif request.POST.get("submit") == "load":
        request.session["celldash_df_data"] = file.open().read().decode("utf-8")
        
        return render(request, "cellviews/components/dash_embed.html")
    
    
