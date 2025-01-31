from pathlib import Path
from io import StringIO

import numpy as np
import plotly.express as px
from plotly import graph_objects as go


def create_hist(df, selected_column):
    """
    Creates a histogram, from 0 to the max value that appears in
    the data.
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
            r=10  # right margin
        ),
        autosize=True,
    )
    return hist, max_value


def create_all_hist_html(df, columns):
    hists = []
    for column in columns:
        hist = create_hist(df, column)
        html = hist.to_json()
        hists.append(html)
    return hists


def generate_heatmap_with_label(labels, matrix, cell_value_text="", decimals:int=1,
                                colorscale=None, gradient_range: None | tuple[
            float | int, float | int] = None):
    """
    Generates a heatmap with a hover label.
    
    The heatmap displays the value of each well, rounded down
    to the passed on amount of decimals.
    
    The labels are used for the rows, columns and cells that
    are displayed. It is also used for the hover information.
    
    On the hover, it displays the row name, column name, cell name
    and it can display the value of the well with a specific name
    attached to it. If no name is passed, this will not be included
    in the hover.
    
    If a value is zero, it will be set as NaN, and it will
    not be displayed in the gradient, this will make it very clear
    that it is zero. The hover however will just simply display
    0.
    
    It displays a passed on colorscale, if passed on.
    If no colorscale is passed on, it will default to a colorscale in
    the LUMC colors. The colorscale can be the name of a plotly
    gradient, or a manually defined gradient.
    
    It's possible to set the range of values for the color gradient.
    By default, it will range from 0 to the maximum value in the
    dataset.
    
    An important part about the code, is that with the way
    that plotly graph objects works, is that the code requires
    reversing the y axis for the visualization to make sense.
    Otherwise it is upside down.
    
    Args:
        labels:
        matrix:
        cell_value_text:
        decimals:
        colorscale:
        gradient_range:

    Returns:

    """
    if decimals is not None:
        matrix = round(matrix, int(decimals))
    
    if colorscale is None:
        colorscale = [
            [0, 'rgb(220, 220, 220)'],
            [1, "rgb(0, 0, 139)"]
        ]  # this is how you set a custom gradient between two colors. 0 being
        # the loewst value.
    
    # colorscale = "gray"
    
    if gradient_range is None:
        gradient_range = [0, matrix.max().max()]
    zmin, zmax = gradient_range
    
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
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax
        # put a different colorscale here if you want a preset
    ))
    
    heatmap_fig.update_layout(
        margin=dict(
            t=10,  # top margin
            b=10,  # bottom margin
            l=10,  # left margin
            r=10  # right margin
        )
    )
    
    return heatmap_fig
