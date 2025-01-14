from pathlib import Path
from io import StringIO

import numpy as np
import plotly.express as px
from plotly import graph_objects as go


def create_hist(df, selected_column):
    """
    Helper function that plots a histogram
    """
    max_value = df[selected_column].max()
    hist = px.histogram(df,
                        range_x=[0, max_value],
                        x=selected_column,
                        title=f'Histogram of {selected_column}',
                        nbins=400)
    
    hist.update_layout(
        margin=dict(
        t=30,  # top margin
        b=10,  # bottom margin
        l=10,  # left margin
        r=10   # right margin
        )
    )
    return hist, max_value


def create_all_hist_html(df, columns):
    hists = []
    for column in columns:
        hist = create_hist(df, column)
        html = hist.to_json()
        hists.append(html)
    return hists


def generate_heatmap_with_label(labels, matrix, cell_value_text=""):
    label_text = [
        [f"Row: {labels[0][i]}<br>" \
         f"Col: {labels[1][j]}<br>" \
         f"Cell: {labels[2][len(labels[1]) * i + j]}"
         for j in range(len(labels[1]))
         ] for i in range(len(labels[0]))
    ]
    
    if cell_value_text:
        label_text = [
            [col +
             f"<br>{cell_value_text}: {matrix.iloc[i, j]}"
             for j, col in enumerate(row)
             ]
            for i, row in enumerate(label_text)
            
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
        texttemplate="%{z}",
    ))
    
    heatmap_fig.update_layout(
        margin=dict(
        t=10,  # top margin
        b=10,  # bottom margin
        l=10,  # left margin
        r=10   # right margin
        )
    )
    
    return heatmap_fig
