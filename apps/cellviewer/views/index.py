import os
import polars as pl
from django.shortcuts import render, HttpResponse
from apps.cellviewer.models.SavedJob import SavedJob
from apps.cellviewer.models.SavedFile import file_dimensions
from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.components.response_modal import ResponseModal
import regex as re

from apps.cellviewer.util.index_helpers import load_and_save_processing
from apps.cellviewer.views.plot_insert_context import plot_insert_element


def index(request):
    """
    The index page.
    Currently the index page is the form that allows
    inputting the file of an experiment, a few buttons need
    to be pressed / inputs gives to get to the actual dashboard.
    
    The index page, will together with the input file
    load the next section of the first page.
    This is done this way because then the inputs are
    based on the actual inputted file.
    
    Args:
        request:

    Returns:

    """
    context = {
        'segment': 'index',
    }
    return render(request, "cellviews/index.html", context)


def index_follow_up_input(request):
    """
    A followup to the index page which renders the main form
    with all the inputs.
    
    It will preprocess the file to check if the request and file
    are in the valid format.
    This is explained more at the function.
    
    This section of the page renders both
    all inputs,
    
    and a table with the first 5 rows of the dataframe.
    
    On the page it is possible to render the dashboard
    with the input labels, and it is possible to save the
    contents to the dashboard.
    
    Args:
        request:

    Returns:

    """
    
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
        "substances": header[3:],
        "table_data": df.head(5).rows(),
        "available_labels": available_labels,
        "row_names": rows,
        "col_names": cols,
        "cell_names": [[f"{row}_{col}" for col in cols] for row in rows]
    }
    
    return render(request, "cellviews/sub_page/index_follow_up_input.html", context)


def load_dash(request):
    """
    Renders the Dash dashboard by being called from the form.
    It will verify separately again that the file fits the format.
    
    Currently it's done through Dash, talks have been had to
    replace Dash with a more Django approach after all, which
    allows for more leniency and flexibility.
    To do so the dashboard needs to be rewritten in either
    Plotly or Bokeh.
    
    django_plotly_dash does not allow sharing memory with the django
    process, it is only possible to communicate through the
    request and sessions objects. This is because the dash app is
    loaded in the page as an embed.
    
    The content of the dataframe is added to the session.
    
    Args:
        request:

    Returns:

    """
    preprocess_response = index_file_preprocess_checking(request)
    if preprocess_response is not None:
        return preprocess_response
    
    files, name, labels, file_name = load_and_save_processing(request)
    
    file = files[0]
    df = pl.read_csv(file)
    
    sub_context = plot_insert_element(
        df, labels,
        file_name=file_name,
        experiment_name=name)
    
    context = {
        **sub_context
    }
    
    return render(request, "cellviews/visualization/base_visualization.html", context)
    

def save_job(request):
    """
    Saves the contents of the file to the database and will respond
    to the user if this has succeeded or failed.
    
    Clicking the button to save should start a popup with a spinner,
    the response is loaded into the modal.
    
    All the inputs on the index page are used to save teh job.
    
    Currently this doens't display very extensive error messages
    if something goes wrong and why.
    This could be added. Right now it will just dump the python error
    if there is no explicit error setup.
    
    Args:
        request:

    Returns:

    """
    preprocess_response = index_file_preprocess_checking(request)
    if preprocess_response is not None:
        return preprocess_response
    
    files, name, labels, _ = load_and_save_processing(request)
    label_matrix_name = request.POST.get("label-layout-name")
    
    substance_cutoffs = request.POST.getlist("substance")
    substance_cutoffs = [substance_cutoffs] # this is because multi file is not
    # done, but savedjob excepts multi file
    
    try:
        saved = SavedJob.objects.create(
            request,
            files,
            substance_cutoffs,
            name,
            labels,
            label_matrix_name
        )
        
        html_content = ResponseModal.render(
            args=("Saved experiment with configuration successfully",
                  f"You can find the saved version at <a "
                  f"href='http://127.0.0.1:8000/saved_jobs/{saved.id}'>saved "
                  f"job</a>")
        )
        
    except Exception as e:
        html_content = ResponseModal.render(
            args=(f"Something went wrong:\n {e} \n Please let the team know if this is unexpected:")
        )
        
    return HttpResponse(html_content)


def index_file_preprocess_checking(request):
    """
    Helper function
    
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
