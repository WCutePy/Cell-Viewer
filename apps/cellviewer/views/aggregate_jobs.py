from django.shortcuts import render, redirect
from apps.cellviewer.models.FilteredFile import FilteredFile
from apps.cellviewer.models.SavedJob import SavedJob
import polars as pl
from functools import reduce


def aggregate_jobs(request):
    job_ids = request.POST.getlist("selected-jobs")
    
    if len(job_ids) < 2:
        return
    
    filtered_files = FilteredFile.objects.filter(job_id__in=job_ids).select_related \
        ('job', 'saved_file')
    
    if filtered_files.count() < 2:
        return
    
    filtered_files: list[FilteredFile] = list(filtered_files)
    first_files_job = filtered_files[0].job
    
    # can expand this to require having the same annotation matrix
    dimension = first_files_job.dimension
    for filtered_file in filtered_files:
        if filtered_file.job.user.id != request.user.id:
            return
        if dimension != filtered_file.job.dimension:
            return
    
    labels = first_files_job.label_matrix
    
    data = filtered_file.generate_filtered_polars_dataframe()
    
    substance_names = data.columns[3:]
    substance_thresholds = filtered_file.substance_thresholds
    
    request.session["celldash_df_data"] = data.write_csv()
    request.session["celldash_labels"] = labels
    
    context = {
        'substances': [(name, threshold) for name, threshold in
                       zip(substance_names, substance_thresholds)],
    }
    
    return render(request, "cellviews/display_saved_job.html", context)