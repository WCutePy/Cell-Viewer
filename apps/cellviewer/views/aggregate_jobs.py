from django.shortcuts import render
from apps.cellviewer.models.FilteredFile import FilteredFile

import pandas as pd

from apps.cellviewer.util.plots import generate_heatmap_with_label
from apps.cellviewer.util.excel_writers import write_comparison_analysis_to_binary


def aggregate_jobs(request):
    """
    
    Args:
        request:

    Returns:

    """
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
    
    substance_names = []
    for filtered_file in filtered_files:
        df = filtered_file.load_polars_dataframe()
    
        well_count_matrix, _, well_count_matrix_percent = (
            filtered_file.get_well_counts_and_percent(df))
        
        matrices.append(
            (well_count_matrix, well_count_matrix_percent)
        )
        substance_names.append(df.columns[3:])
    
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
    
    individual_file_info = [
        [f.original_file_name for f in filtered_files],
        [f.job.name for f in filtered_files],
        
    ]

    excell_content = write_comparison_analysis_to_binary(
        file_names=individual_file_info[0],
        experiment_names=individual_file_info[1],
        substance_names=substance_names,
        substance_thresholds=[f.get_substance_thresholds_as_list for f in filtered_files],
        individual_matrix_explanations=[["Double positive percent"] for f in filtered_files],
        individual_matrices=[[percent] for count, percent in matrices],
        matrix_explanations=["Mean of double positive percentages",
                             "Standard deviation of double positive percentages"],
        matrices=[mean_matrix, std_matrix]
    )
    
    # this works through magic
    reshaped_substance_info = [
        [[name, threshold] for name, threshold in
         zip(sub_name, thresholds)]
        for sub_name, thresholds in
        zip(substance_names, [f.get_substance_thresholds_as_list for f in filtered_files])
    ]

    individual_file_info = list(zip(
        [f.original_file_name for f in filtered_files],
        [f.job.name for f in filtered_files],
        reshaped_substance_info
    ))

    context = {
        "mean_heatmap": mean_heatmap.to_html(),
        "std_heatmap": std_heatmap.to_html(),
        "excell_content": excell_content,
        "individual_file_info": individual_file_info,
    }
    
    return render(request, "cellviews/aggregate_jobs.html", context)


