from django.shortcuts import render, redirect
from apps.cellviewer.models.FilteredFile import FilteredFile
from apps.cellviewer.models.SavedJob import SavedJob
import polars as pl
from functools import reduce


import numpy as np
from dash import Dash, dcc, html, Input, Output, \
    callback, no_update, State
from pathlib import Path
from io import StringIO
import pandas as pd
import json
import os
import shutil
import plotly.express as px
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from django.core.exceptions import SuspiciousOperation
from io import StringIO
from plotly import graph_objects as go


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
        if filtered_file.job.user.id != request.user.id:
            return
        if dimension != filtered_file.job.dimension:
            return
    
    labels = first_files_job.label_matrix.get_labels
    
    matrices = []
    
    for filtered_file in filtered_files:
    
        well_count_matrix, well_count_matrix_percent = (
            filtered_file.get_well_count_and_well_count_percent())
        
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


def generate_heatmap_with_label(labels, matrix, additional_text):
    base_label_text = [
        [f"Row: {labels[0][i]}<br>" \
         f"Col: {labels[1][j]}<br>" \
         f"Cell: {labels[2][len(labels[1]) * i + j]}"
         for j in range(len(labels[1]))
         ] for i in range(len(labels[0]))
    ]
    
    label_text = [
        [col +
         f"<br>{additional_text}: {matrix.iloc[i, j]}"
         for j, col in enumerate(row)
         ]
        for i, row in enumerate(base_label_text)
    ]
    """
    It is required to invert everything related to the y column, as go.heatmap works from bottom to top.
    There might be a smoother way to solve this but I was not able to find one.
    """
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=np.where(matrix == 0, None,
                   matrix)[::-1],
        x=labels[1],
        y=labels[0][::-1],
        hoverinfo='text',
        text=label_text[::-1],
    ))
    
    return heatmap_fig
