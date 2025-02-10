import os

from django.http import HttpResponse

from apps.cellviewer.components.label_matrix_input_fields import \
    LabelMatrixInputFieldsComponent
from apps.cellviewer.models.LabelMatrix import LabelMatrix


def load_and_save_processing(request):
    """
    Helper function
    
    A function that extracts values from the request.
    The function was created to reduce certain code duplication,
    and make it easier to change the behaviour or names across the
    multiple functions.
    Args:
        request:

    Returns: The files, The job/experiment name, the labels

    """
    
    files = request.FILES.getlist("inputData")
    name = request.POST.get("name")
    
    default_labels, labels = load_labels_from_request(request)
    
    file_name = files[0].name
    if not name:
        name_without_extension, _ = os.path.splitext(file_name)
        name = name_without_extension + "_experiment"
    
    return files, name, labels, file_name


def load_labels_from_request(request):
    """
    Helper function
    
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
        A tuple of the default rows names
        A tuple of the default col names
        A tuple containing a tuple of the rows, cols and cell names

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


def stored_label_matrix_as_html(request):
    """
    Generates a new label matrix for annotation with
    preselected inputs based on a label matrix loaded from
    the database.
    It's done by generating it in python to require less javascript
    to swap the elements individually.
    
    Generates the html for this.
    This is currently in util, but something accessed by
    a url shouldn't be in util. This was put here accidentally.
    Consider moving this in the future.
    
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
