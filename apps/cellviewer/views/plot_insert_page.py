from typing import Any

import polars as pl
from django.shortcuts import render, HttpResponse

from apps.cellviewer.models.FilteredFile import FilteredFile
from apps.cellviewer.util.excel_writers import \
    write_individual_analysis_to_binary
from apps.cellviewer.util.plots import create_hist, generate_heatmap_with_label
from apps.cellviewer.util.well_count_matrices import filtered_polars_dataframe, \
    generate_well_counts_and_percent
from apps.cellviewer.util.index_helpers import load_and_save_processing


def plot_insert_element(df: pl.dataframe, labels,
                        substance_thresholds: list[float] = None,
                        include: list[str]=("all",),
                        experiment_name=None
                        ):
    """
    Does not directly render a view.
    Creates the necessary context to use the include of the
    visualization page base_visualization.html
    
    This function expects all the information
    that could be necessary to render page to be preprocessed
    in their expected formats.
    
    It is possible to get the full context, or only get a part of
    the context. This is done because some information,
    such as the filtered heatmaps, is expected to be reloaded
    multiple times with different values. As this is the case,
    it would not be smart or recommended to also recreate the histograms
    every time when they remain unused.
    The variable include is used for this, however the standar
    is rather unclear.
    Currently, it is set as a tuple of seperate elements,
    so it might be possible in the future to frankestein multiple
    parts together.
    However currently this is irrelevant, as there are two options.
    
    A filter threshold, this is the filter to apply to calculate the
    double positives.
    
    It creates multiple visualizations.
    Histograms for each substance, showing the value distribution.
    The page has sliders allowing you to set the value.
    
    Heatmap for the total count, the filtered count
    and the amount of double positives.
    
    The page has buttons to allow downloading the files.
    This also sends the content of said files
    
    Args:
        df: a polars dataframe
        labels: The labels in the list format [row, col, cells]
        substance_thresholds: a list with floats
        include: a list of strings for the elements.
            Leaving this empty gives all.
        experiment_name:
    
    Returns:
        context dictionary to be used in combination with the
        base_visualiation.html

    """
    substances = df.columns[3:]
    amount_of_sites = df["Site"].max()
    
    if substance_thresholds is None:
        substance_thresholds = (0,) * len(substances)
    
    context = {
    }
    
    if "all" in include or "hist" in include:
        histograms_data = []
        for substance, threshold in zip(substances, substance_thresholds):
            hist, max_value = create_hist(
                df, substance
            )
            histograms_data.append(
                (substance, hist.to_html(), max_value, threshold)
            ) # this order is important for the rendering.
        
        context.update({
            "histogram_data": histograms_data,
        })
    
    well_count_matrix, filtered_well_count_matrix, \
        well_positives_percent = (
        generate_well_counts_and_percent(
            df, substance_thresholds
        ))
    
    if "all" in include:
        context.update({
            "heatmap_total_cell_counts": generate_heatmap_with_label(
                labels, well_count_matrix, "Count"
            ).to_html(),
            "file_count_matrix": well_count_matrix.to_csv(),
        })
        
    matrix_explanations = [
        "Well counts per well",
        "Well counts filtered on the substance thresholds",
        "Double positives above the thresholds"
    ]
    matrices = [well_count_matrix, filtered_well_count_matrix,
                well_positives_percent]
    
    excel_file_content = write_individual_analysis_to_binary(
        experiment_name=experiment_name,
        substance_names=substances, substance_thresholds=substance_thresholds,
        matrix_explanations=matrix_explanations,
        matrices=matrices
    )
    
    context.update({
        "substances_str": " and ".join(substances),
        "sub_and_threshold_str": " and ".join(
            f"{a} for {b}" for a, b in zip(substance_thresholds, substances)
        ),
        "amount_of_sites": amount_of_sites,
        
        "heatmap_filtered_cell_counts": generate_heatmap_with_label(
            labels, filtered_well_count_matrix, "Count"
        ).to_html(),
        "file_filtered_counts": filtered_well_count_matrix.to_csv(),
        
        "heatmap_percentage": generate_heatmap_with_label(
            labels, well_positives_percent, "Count"
        ).to_html(),
        "file_double_positives": well_positives_percent.to_csv(),
        
        "file_all": excel_file_content,
        
        "job_id": "-1",
        "name": experiment_name,
    })
    
    return context


def update_filtered_plots(request):
    """
    Renders the page element of the filtered plots.
    Loads base_visualization_filtered_part.html
    Sending in the context only the rquired information.
    
    It is possible to call from both a not saved,
    and a saved file.
    If it has been saved the job id will be a non -1
    integer, if it has not been saved it is -1.
    
    When it has not been saved, it will load the information
    relevant through the same function the index load
    function uses. As such, thanks to the reuse, this function
    has been abstracted to utils.
    
    If it has been saved, it uses the same methodology that
    saved_jobs uses to load the data. Currently, this is
    not a function yet, however this too should be abstracted
    for consistency. Currently, there is code duplication
    
    After having the info loaded,
    It only renders the plots that are relevant and created the
    filtered part of the page.
    
    This is done this way to not require reloading the full page
    everytime.
    It does reload a part, instead of updating the plots on
    the client side, and that is okay. This is as, to more performant
    than using Dash is, and more performance is currently not required.
    
    For better performance, and for more customizability,
    all visualization, or atleast the visualizations that require
    a great deal of interaction or customizability should be rendered
    or updated through javascript.
    The current interaction functions the same dash does
    their callbacks. So it's not particularly Django behaviour.
    I didn't do it with JavaScript, as it would add more to the
    application in learning curve, and it would take me more time
    to rewrite from Dash to JavaScript than putting this
    together.
    
    The updated section is loaded through HTMX. A simple way
    to update a section of a page without JavaScript.
    
    Args:
        request:

    Returns:

    """
    if request.POST.get("job_id") == "-1":
        files, name, labels = load_and_save_processing(request)
        
        print(name)
        
        df = pl.read_csv(files[0])
        
        if not name:
            name = "unnamed"
    
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
        
        name = job.name
    
    substance_thresholds = [float(i) for i in
                           request.POST.getlist("substance_threshold")]
    
    context = plot_insert_element(df, labels, substance_thresholds, experiment_name=name)
    return render(request,
                  "cellviews/visualization/base_visualization_filtered_part.html",
                  context)
