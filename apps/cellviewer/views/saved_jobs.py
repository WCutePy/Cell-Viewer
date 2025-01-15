from django.shortcuts import render, redirect
from apps.cellviewer.models.FilteredFile import FilteredFile
from apps.cellviewer.models.SavedJob import SavedJob
import polars as pl
from functools import reduce

from apps.cellviewer.views.plot_insert_page import plot_insert_element


def saved_jobs(request):
    """
    Gets all of a user jobs and displays them in a table.
    To be able to display the job and link to it, but not display the
    id to the user as this adds no value,
    the template iterates over parts of the jobs
    list. This is a bit convoluted but adds simplicity to the template itself.
    
    so id matches with name
    label_matrix_id matches with label_matrix__matrix_name
    
    and every other field just iterates normally
    Args:
        request:

    Returns:

    """
    jobs = SavedJob.objects.get_all_jobs_for_user(request.user).select_related("label_matrix")
    fields = ["id", "label_matrix_id", "name", "label_matrix__matrix_name", "date", "dimension"]
    headers = ["name", "annotation", "date", "dimension", "loi"]
    jobs = jobs.values(*fields)
    
    data = (
        list(job.values())
        for job in jobs[::-1]
    )
    
    context = {
        "header": headers,
        'jobs': data,
        'segment': 'stored',
    }
    return render(request, "cellviews/saved-jobs.html", context)


def display_job(request, job_id: int):
    """
    Renders the page for a specific job
    It checks if the job exists, and if the job
    has been created by the user. If the job does not
    belong to the user the page will not render.
    
    It will load the content of the file, and filter it
    based on the thresh holds.
    It will send the filtered file as text to Dash.
    
    Args:
        request:
        job_id:

    Returns:

    """
    filtered_files = FilteredFile.objects.filter(job_id=job_id).select_related('job', 'saved_file')

    if filtered_files.count() == 0:
        return
    filtered_file: FilteredFile = filtered_files.first()
    job = filtered_file.job
    if job.user.id != request.user.id:
        return
    
    labels = job.label_matrix.get_labels
    
    df = filtered_file.load_polars_dataframe()
    
    substance_names = df.columns[3:]
    substance_thresholds = filtered_file.get_substance_thresholds_as_list
    
    sub_context = plot_insert_element(
        df, labels, pre_filter_substance_threshold=substance_thresholds, name=job.name
    )
    
    context = {
        'substances': [(name, threshold) for name, threshold in
                       zip(substance_names, substance_thresholds)],
        **sub_context,
        "job_id": job_id
    }

    return render(request, "cellviews/display_saved_job.html", context)


def delete_job(request, job_id: int):
    """
    Deletes a job if it exists based on its id.
    
    Will check that the job belongs to the user before deleting.
    It lets the SavedJob class handle the deletion.
    Args:
        request:
        job_id:

    Returns:

    """
    job = SavedJob.objects.filter(id=job_id)
    
    if job.count() == 0:
        return
    job = job.first()
    if job.user.id != request.user.id:
        return

    job.delete()
    
    return redirect("cellviewer:saved_jobs")
