import polars as pl
from django.shortcuts import render, HttpResponse
from apps.cellviewer.models.SavedJob import SavedJob, file_dimensions
from apps.cellviewer.models.LabelMatrix import LabelMatrix
from components.label_matrix_input_fields import LabelMatrixInputFieldsComponent


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
    
    df = pl.read_csv(file)
    
    header = df.columns
    
    _, (rows, cols) = file_dimensions(df)
    
    available_labels = LabelMatrix.objects.get_all_same_size(request.user, len(rows), len(cols))
    print(available_labels)
    
    context = {
        "header": header,
        "table_data": df.head(5).rows(),
        "available_labels": available_labels,
        "row_names": rows,
        "col_names": cols,
        "cell_names": [[f"{row}_{col}" for col in cols] for row in rows],
        "default_rows": ",,,".join(rows),
        "default_cols": ",,,".join(cols),
    }
    
    return render(request, "cellviews/components/save_and_request_dash_app.html", context)


def load_dash(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    files, name, labels = load_and_save_processing(request)
    
    request.session["celldash_df_data"] = files[0].open().read().decode("utf-8")
    
    # request.session["celldash_default_labels"] = default_labels
    request.session["celldash_labels"] = labels
    
    return render(request, "cellviews/components/dash_embed.html")
    

def save_job(request):
    if request.method != "POST":
        return
    if "inputData" not in request.FILES:
        return
    
    files, name, labels = load_and_save_processing(request)
    label_matrix_name = request.POST.get("label-layout-name")
    
    SavedJob.objects.create(
        request,
        files,
        name,
        labels,
        label_matrix_name
    )
    return HttpResponse()


def load_and_save_processing(request):
    files = request.FILES.getlist("inputData")
    name = request.POST.get("name")
    
    default_rows = request.POST.get("default-rows").split(",,,")  # this is to allow "," inside of the names.
    default_cols = request.POST.get("default-cols").split(",,,")
    
    rows = [a if a else b for a, b in zip(request.POST.getlist("row"), default_rows)]
    cols = [a if a else b for a, b in zip(request.POST.getlist("col"), default_cols)]
    cells = [a if a else rows[i // len(cols)] + "_" + cols[i % len(cols)] for i, a in
             enumerate(request.POST.getlist("cell"))]
    
    default_labels = (tuple(default_rows), tuple(default_cols))
    labels = (tuple(rows), tuple(cols), tuple(cells))
    return files, name, labels


def load_stored_label_matrix(request):
    matrix_id = int(request.POST.get("label-select"))
    
    matrix = LabelMatrix.objects.get(pk=matrix_id)
    rows, cols, cells = matrix.get_labels
    matrix_name = matrix.matrix_name
    cells = [cells[i * len(cols):(i + 1) * len(cols)] for i in range(len(rows))]
    
    html_content = LabelMatrixInputFieldsComponent.render(
        args=[matrix_name, rows,cols,cells]
    )
    
    return HttpResponse(html_content)