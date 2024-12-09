from django.shortcuts import render, redirect
from apps.cellviewer.models.SavedJob import SavedJob


def saved_jobs(request):
    jobs = SavedJob.objects.get_all_jobs_for_user(request.user)
    headers = ["id", "name", "date", "dimension"]
    jobs = jobs.values(*headers)
    
    jobs = list(list(job.values()) for job in jobs)
    
    context = {
        "header": headers[1:],
        'jobs': jobs,
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
    
    return redirect(saved_jobs)
