import polars as pl
from django.shortcuts import render
from cellviewer.models.SavedJob import SavedJob, file_dimensions


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
    
    # needs removal
    # file = "240306-EXP3-2-plate_1output.csv"
    
    df = pl.read_csv(file)
    
    header = df.columns
    
    _, dimensions = file_dimensions(df)
    
    context = {
        "header": header,
        "table_data": df.head(5).rows(),
        "dimensions": dimensions,
        "default_rows": ",,,".join(dimensions[0]),
        "default_cols": ",,,".join(dimensions[1]),
    }
    
    return render(request, "cellviews/components/save_and_request_dash_app.html", context)


def load_dash(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    file, name, labels = load_and_save_processing(request)
    
    request.session["celldash_df_data"] = file.open().read().decode("utf-8")
    
    # request.session["celldash_default_labels"] = default_labels
    request.session["celldash_labels"] = labels
    
    return render(request, "cellviews/components/dash_embed.html")
    

def save_job(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    file, name, labels = load_and_save_processing(request)
    
    SavedJob.objects.create(
        request,
        file,
        name,
        labels
    )
    return


def load_and_save_processing(request):
    file = request.FILES["inputData"]
    name = request.POST.get("name")
    
    default_rows = request.POST.get("default-rows").split(",,,")  # this is to allow "," inside of the names.
    default_cols = request.POST.get("default-cols").split(",,,")
    
    rows = [a if a else b for a, b in zip(request.POST.getlist("row"), default_rows)]
    cols = [a if a else b for a, b in zip(request.POST.getlist("col"), default_cols)]
    cells = [a if a else rows[i // len(cols)] + "_" + cols[i % len(cols)] for i, a in
             enumerate(request.POST.getlist("cell"))]
    
    default_labels = (tuple(default_rows), tuple(default_cols))
    labels = (tuple(rows), tuple(cols), tuple(cells))
    return file, name, labels
