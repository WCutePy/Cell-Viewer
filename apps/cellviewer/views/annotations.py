from django.shortcuts import render, redirect
from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.views.index import load_labels_from_request


def saved_annotations_page(request):
    """
    Renders a page with all annotations.
    
    It queries the database for all annotations of a user.
    The page displays headers relating to the fields, and
    the values.
    
    The annotation page displays a table with the information
    and a link to the individual annotation.
    
    Args:
        request:

    Returns:

    """
    annotations = LabelMatrix.objects.get_all_of_user(request.user)

    fields = ["id", "matrix_name", "dimension_string", "public",
               "keep_when_unused"]
    headers = ["name", "dimension", "publicly available", "will remain if unused"]
    annotations = (annotations.values_list(*fields))
    
    context = {
        "header": headers,
        'jobs': annotations,
        'segment': 'annotations',
    }
    return render(request, "cellviews/saved_annotations.html", context)


def annotation_page(request, annotation_id: int):
    annotation = LabelMatrix.objects.get(id=annotation_id)

    if annotation.created_by.id != request.user.id:
        return
    
    rows, cols, cells = annotation.get_labels_with_2d_cells

    context = {
        "annotation_name": annotation.matrix_name,
        "row_names": rows,
        "col_names": cols,
        "cell_names": cells,
        "keep_when_unused": annotation.keep_when_unused,
        "public": annotation.public,
    }

    return render(request, "cellviews/display_saved_annotation.html", context)


def edit_annotation(request, annotation_id: int):
    annotation = LabelMatrix.objects.get(id=annotation_id)

    if annotation.created_by.id != request.user.id:
        return
    
    name = request.POST.get("label-layout-name")
    _, labels = load_labels_from_request(request)
    
    print(name)
    
    keep_when_unused = request.POST.get('keep_when_unused') is not None
    public = request.POST.get('public') is not None
    
    annotation.update(*labels, name, keep_when_unused, public)
    
    return redirect("cellviewer:annotation_page", annotation_id)
