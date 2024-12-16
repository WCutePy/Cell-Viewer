from django.shortcuts import render, redirect
from apps.cellviewer.models.SavedJob import SavedJob


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
    print(jobs)
    
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
    job = SavedJob.objects.filter(id=job_id)
    
    if job.count() == 0:
        return
    job = job.first()
    if job.user.id != request.user.id:
        return
    
    file = job.files.first().file
    labels = job.label_matrix.get_labels
    request.session["celldash_df_data"] = file.open().read().decode("utf-8")
    request.session["celldash_labels"] = labels
    return render(request, "cellviews/display_saved_job.html")


def delete_job(request, job_id: int):
    job = SavedJob.objects.filter(id=job_id)
    
    if job.count() == 0:
        return
    job = job.first()
    if job.user.id != request.user.id:
        return

    job.delete()
    
    return redirect("cellviewer:saved_jobs")
