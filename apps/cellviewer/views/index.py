import polars as pl
from django.shortcuts import render, HttpResponse
from apps.cellviewer.models.SavedJob import SavedJob, file_dimensions
from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.components.label_matrix_input_fields import LabelMatrixInputFieldsComponent
from apps.cellviewer.components.response_modal import ResponseModal
import regex as re


def index(request):
    context = {
        'segment': 'index',
    }
    return render(request, "cellviews/index.html", context)


def index_follow_up_input(request):
    preprocess = index_file_preprocess_checking(request)
    if preprocess is not None:
        return preprocess
    
    file = request.FILES.getlist("inputData")[0]
    df = pl.read_csv(file)
    
    header = df.columns
    
    _, (rows, cols) = file_dimensions(df)
    
    available_labels = LabelMatrix.objects.get_all_same_size(request.user, len(rows), len(cols))
    
    context = {
        "header": header,
        "table_data": df.head(5).rows(),
        "available_labels": available_labels,
        "row_names": rows,
        "col_names": cols,
        "cell_names": [[f"{row}_{col}" for col in cols] for row in rows]
    }
    
    return render(request, "cellviews/sub_page/index_follow_up_input.html", context)


def load_dash(request):
    preprocess = index_file_preprocess_checking(request)
    if preprocess is not None:
        return preprocess
    
    files, name, labels = load_and_save_processing(request)
    
    request.session["celldash_df_data"] = files[0].open().read().decode("utf-8")
    
    # request.session["celldash_default_labels"] = default_labels
    request.session["celldash_labels"] = labels
    
    return render(request, "cellviews/sub_page/dash_embed.html")
    

def save_job(request):
    preprocess = index_file_preprocess_checking(request)
    if preprocess is not None:
        return preprocess
    
    files, name, labels = load_and_save_processing(request)
    label_matrix_name = request.POST.get("label-layout-name")
    
    saved = SavedJob.objects.create(
        request,
        files,
        name,
        labels,
        label_matrix_name
    )
    
    html_content = ResponseModal.render(
        args=("Saved experiment with configuration successfully",
              f"You can find the saved version at <a href='http://127.0.0.1:8000/saved_jobs/{saved.id}'>saved job</a>")
    )
    
    return HttpResponse(html_content)


def load_and_save_processing(request):
    files = request.FILES.getlist("inputData")
    name = request.POST.get("name")
    
    default_labels, labels = load_labels_from_request(request)
    
    return files, name, labels


def load_labels_from_request(request):
    """
    This will compare the default row and column
    values with the inputted values from the inputs.
    If something is not inputted, it will fall back to
    the default value. Otherwise the value will be the
    intended value. It has to be done this way
    to allow the input matrix to not have every value inputted
    from the start.
    Args:
        request:

    Returns:

    """
    default_rows = request.POST.get("default-rows").split(
        ",,,")  # this is to allow "," inside of the names.
    default_cols = request.POST.get("default-cols").split(",,,")
    
    rows = [a if a else b for a, b in
            zip(request.POST.getlist("row"), default_rows)]
    cols = [a if a else b for a, b in
            zip(request.POST.getlist("col"), default_cols)]
    cells = [a if a else rows[i // len(cols)] + "_" + cols[i % len(cols)] for
             i, a in
             enumerate(request.POST.getlist("cell"))]
    labels = (tuple(rows), tuple(cols), tuple(cells))
    
    return (tuple(default_rows), tuple(default_cols)), labels


def load_stored_label_matrix(request):
    """
    Generates a new label matrix for annotation with
    preselected inputs based on a label matrix loaded from
    the database.
    It's done by generating it in python to require less javascript
    to swap the elements individually.
    Args:
        request:

    Returns:

    """
    matrix_id = int(request.POST.get("label-select"))
    
    matrix = LabelMatrix.objects.get(pk=matrix_id)
    rows, cols, cells = matrix.get_labels_with_2d_cells
    matrix_name = matrix.matrix_name
    
    html_content = LabelMatrixInputFieldsComponent.render(
        args=(matrix_name, rows, cols, cells)
    )
    
    return HttpResponse(html_content)


def index_file_preprocess_checking(request):
    """
    Will go through a list of checks in a preprocessing
    state to ensure that the inputs fit the format properly.
    Sometimes it's possible for something to be "accepted" and
    not throw an error yet without being the correct format.
    
    This applies to the file contents in particular.
    If this error checking is not done, it is possible to
    load an improper dash application,
    or to save a wrongly formatted file to the database.
    
    It adds an overhead as a result of checking the full file
    content.
    
    It checks the request method, the presence of the files.
    It checks if all files have the required header.
    And if the content matches the pattern as described in regex.
    Currently it demands
    Args:
        request:

    Returns:

    """
    response_title = ""
    response_text = ""
    if request.method != "POST":
        response_title = "Error, Improper request method"
        response_text += "The request is not a post"
    elif "inputData" not in request.FILES:
        response_title = "Error missing file"
        response_text += "Missing file input"
        
    for file in request.FILES.getlist("inputData", []):
        header = file.file.readline().decode("utf-8").strip().split(",")
        print(header)
        print(header)
        if header[:3] != ["Well", "Site", "Cell"]:
            response_title = "Wrong file header"
            response_text += ("The file header does not start with Well,Site,"
                              "Cell")
            break
        
        content = file.file.read().decode("utf-8")
        
        file.file.seek(0)
        n = len(header) - 3
        match_line = fr"[A-Z]\d{{,3}},\d+,\d+(,{r"\d+\.?\d*"}){{{n}}}"
        match_enter = r"(\r\n|\r|\n)"
        pattern = fr"^({match_line}{match_enter})+({match_line}{match_enter}?)$"
        file_format_match = re.fullmatch(pattern, content)
        
        if file_format_match is None:
            response_title = "Wrong file format"
            response_text += ("There is a mistake in the file somewhere, "
                              "a "
                              "mistaken input is somewhere ")
    
    if response_title or response_text:
        html_content = ResponseModal.render(
            args=(response_title, response_text)
        )
        
        return HttpResponse(html_content)
    return None
