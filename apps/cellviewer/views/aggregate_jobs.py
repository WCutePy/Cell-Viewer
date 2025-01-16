from django.shortcuts import render
from apps.cellviewer.models.FilteredFile import FilteredFile

import pandas as pd

from apps.cellviewer.util.plots import generate_heatmap_with_label


def aggregate_jobs(request):
    job_ids = request.POST.getlist("selected-jobs")
    # job_ids = ["11", "13"]

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
        if not filtered_file.job.is_viewable_by(request.user):
            return
        if dimension != filtered_file.job.dimension:
            return
    
    labels = first_files_job.label_matrix.get_labels
    
    matrices = []
    
    for filtered_file in filtered_files:
    
        well_count_matrix, _, well_count_matrix_percent = (
            filtered_file.get_well_counts_and_percent())
        
        matrices.append(
            (well_count_matrix, well_count_matrix_percent)
        )
        
        print("just to show")
        print(well_count_matrix)
        print(well_count_matrix_percent)
    
    mean_matrix = pd.DataFrame(0, index=matrices[0][0].index,
                               columns=matrices[0][0].columns)
    
    for well_count_matrix, well_count_matrix_percent in matrices:
        mean_matrix += well_count_matrix_percent
    
    mean_matrix /= len(matrices)
    
    std_matrix = pd.DataFrame(0, index=matrices[0][0].index,
                              columns=matrices[0][0].columns)
    
    for well_count_matrix, well_count_matrix_percent in matrices:
        std_matrix += (well_count_matrix_percent - mean_matrix) ** 2
    
    std_matrix = (std_matrix / len(matrices)) ** 0.5
    
    
    mean_heatmap = generate_heatmap_with_label(labels, mean_matrix, "Mean percentage")
    
    std_heatmap = generate_heatmap_with_label(labels, std_matrix, "Std")
    

    context = {
        "mean_heatmap": mean_heatmap.to_html(),
        "std_heatmap": std_heatmap.to_html(),
    }
    
    return render(request, "cellviews/aggregate_jobs.html", context)


