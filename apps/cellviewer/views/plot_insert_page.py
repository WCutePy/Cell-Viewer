from typing import Any

import polars as pl
from django.shortcuts import render, HttpResponse

from apps.cellviewer.models.FilteredFile import FilteredFile
from apps.cellviewer.util.plots import create_hist, generate_heatmap_with_label
from apps.cellviewer.util.well_count_matrices import filtered_polars_dataframe, \
    generate_well_counts_and_percent
from apps.cellviewer.util.index_helpers import load_and_save_processing


def plot_insert_element(df: pl.dataframe, labels,
                        pre_filter_substance_threshold=None,
                        substance_threshold=None,
                        include=["all"]
                        ):
    """
    Does not directly render a view.
    Creates the necessary context to use the include dash_embed (to be changed).
    
    Through the use of being saved to the database,
    but also by the data not being saved and sent by the user every
    time. The latter is more inefficient than the prior.
    This page does not handle this part and simply generates
    the plot section.
    This makes it possible for the surrounding infrastructure to
    change.
    
    Another function to generate an updated double positive
    heatmap will be below. This too requires the pre
    handling of variables.
    
    
    Args:
        df:

    Returns:

    """
    
    "histogram_data =  [substance_name, histogram, max_value]"
    
    if pre_filter_substance_threshold is None:
        pre_filter_substance_threshold = (0, 0)
    
    original_df = df
    df = filtered_polars_dataframe(df, pre_filter_substance_threshold)
    
    if substance_threshold is None:
        substance_threshold = [0, 0]
    
    substances = df.columns[3:]
    
    context = {
    }
    
    if "all" in include or "hist" in include:
        histograms_data = []
        for substance in substances:
            hist, max_value = create_hist(
                df, substance
            )
            histograms_data.append(
                (substance, hist.to_html(), max_value)
            )
        
        context.update({
            "histogram_data": histograms_data,
        })
    
    well_count_matrix, filtered_well_count_matrix, \
        well_count_matrix_percent = (
        generate_well_counts_and_percent(
            df, substance_threshold
        ))
    
    if "all" in include:
        context.update({
            "heatmap_total_cell_counts": generate_heatmap_with_label(
                labels, well_count_matrix, "Count"
            ).to_html(),
        })
    
    context.update({
        "substances_str": " and ".join(substances),
        "sub_and_threshold_str": " and ".join(
            f"{a} for {b}" for a, b in zip(substance_threshold, substances)
        ),
        "heatmap_filtered_cell_counts": generate_heatmap_with_label(
            labels, filtered_well_count_matrix, "Count"
        ).to_html(),
        "heatmap_percentage": generate_heatmap_with_label(
            labels, well_count_matrix_percent, "Count"
        ).to_html(),
        "job_id": "-1",
    })
    
    return context


def update_filtered_plots(request):
    """
    Handles the updating of the filtered plots.
    This is currently done through python.
    For better performance, and to potentially have the
    code be less "weird", it could be better
    to perform this operation through JavaScript.
    Doing it through JavaScript is preferred, however
    to not add new systems which might be unknown, it is
    currently performed similar to how Dash does it.
    
    The callback however did need to be manually written.
    
    Args:
        request:

    Returns:

    """
    if request.POST.get("job_id") == "-1":
        files, name, labels = load_and_save_processing(request)
        pre_filter_substance_threshold = None
        
        df = pl.read_csv(files[0])
        
    else:
        # duplicates part with saved_jobs, find a better way
        # to do this.
        job_id = int(request.POST.get("job_id"))
        filtered_files = FilteredFile.objects.filter(
            job_id=job_id).select_related('job', 'saved_file')
        
        if filtered_files.count() == 0:
            return
        filtered_file: FilteredFile = filtered_files.first()
        job = filtered_file.job
        if job.user.id != request.user.id:
            return
        
        labels = job.label_matrix.get_labels
        
        df = filtered_file.load_polars_dataframe()
        
        pre_filter_substance_threshold = filtered_file.get_substance_thresholds_as_list
    
    substance_threshold = [float(i) for i in request.POST.getlist("substance_threshold")]
    
    context = plot_insert_element(df, labels, pre_filter_substance_threshold,
                                  substance_threshold)
    return render(request, "cellviews/visualization/base_visualization_filtered_part.html", context)
    
    