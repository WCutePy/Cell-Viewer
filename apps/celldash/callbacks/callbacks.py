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

width_histogram = 5
UPlOAD_FOLDER_ROOT = '/tmp/uploads/'
UPlOAD_FOLDER_STORE = '/tmp/store/'
Path(UPlOAD_FOLDER_ROOT).mkdir(parents=True, exist_ok=True)

# Initialize the Dash app
# Notice suppress_callback_exceptions=True, this might need to be turned off 
# for future debugging
app = DjangoDash(
    name="CellDash",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    # suppress_callback_exceptions=True,
)

# only load columns of interest
use_cols = ["Well", "Site", "Cell", "OCT4", "SOX17"]


@app.callback(
    [Output('intermediate-value', 'data'),
     Output("title_element", "children"),
    Output("slider-1", "children"),
    Output("slider-2", "children"),
    Output("double_positive_text", "children"),
     ],
    [Input('uploaded', "n_clicks")],
)
def on_page_load(n, request):
    """
    This is the main difference in dash between the original
    dash application and what has been added to it.
    
    When the Dash application is loaded, a button in the dash_app
    will trigger this callback, initializing the intermediate-value
    with all the data.
    
    django_plotly_dash does not allow sharing memory with the django
    process, it is only possible to communicate through the
    request and sessions objects. This is because the dash app is
    loaded in the page as an embed.

    The initial request was for no data to get stored to disk
    unless necessary.
    It could have been possible to write it to disk and have
    Django automatically clean it after a reasonable time (this route
    might be preferred if upscaling was a bigger priority).
    Currently it communicates the whole content of the file
    through the session as the string.
    
    After a dataframe has been made out of it, it will
    be removed from the  session.
    
    The same is done for the labels.
    
    The strings of certain elements get replaced
    by this callback as well, to have them reflect the actual
    variable name passed on. Sadly if loading the page takes long
    the default of OCT7 will still be seen clearly first.
    
    Args:
        n:
        request:

    Returns:

    """
   
    df_content = request.session.get("celldash_df_data", None)
    if df_content is None:
        raise SuspiciousOperation("The celldash_df_data has not been set")
    
    df = pd.read_csv(StringIO(df_content))
    del request.session["celldash_df_data"]
    
    labels = request.session["celldash_labels"]
    # default_labels = request.session["celldash_default_labels"]
    del request.session["celldash_labels"]
    # del request.session["celldash_default_labels"]
    
    substances = df.columns[3:]
    sub1, sub2, *_ = substances
    
    sox17_max = df[sub1].max()
    oct4_max = df[sub2].max()
    df_dump = df.to_json(orient='split')
    df_dump_filename = {
        'df': df_dump,
        'filename': "",
        'sox17_max': sox17_max,
        'oct4_max': oct4_max,
        'labels': labels,
        # 'default_labels': default_labels,
    }
    
    return [json.dumps(df_dump_filename),
            f'Histograms of {sub1} and {sub2} intensity values',
            f"Select {sub1} min",
            f"Select {sub2} min",
            f"""The percentage of cells that are double positive
           ({sub1} and {sub2} above the set threshold)""",
            ]


@app.callback(
    [Output('head-table', 'columns'),
     Output('head-table', 'data'),
     Output('file-description', 'children')],
    [Input('intermediate-value', 'data')]
)
def load_data(jsonified_df):
    if jsonified_df is None:
        return no_update, no_update, no_update
    
    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    cols = [{'name': i, 'id': i} for i in df.columns]
    head_table = df.head().to_dict('records')
    n_rows = df.shape[0]
    file_info_text = f"File has a  total of {n_rows} rows. The first 5 are shown below"
    return cols, head_table, file_info_text


# Callback to update the histogram A plot based on the selected column
@app.callback(
    [Output('histogram-plot-a', 'figure'),
     Output('histogram-plot-b', 'figure')],
    [Input('intermediate-value', 'data')]
)
def update_histogram(jsonified_df):
    if jsonified_df is None:  # or selected_column is None:
        return no_update
    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    hist_oct4 = create_hist(df, selected_column=df.columns[3])
    hist_sox17 = create_hist(df, selected_column=df.columns[4])
    return hist_oct4, hist_sox17


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
    return hist


@app.callback(Output('OCT4-slider', 'children'),
              Input('intermediate-value', 'data')
              )
def create_oct4_slider(jsonified_df):
    if jsonified_df is None:
        oct4_max = 5
    else:
        df_filename = json.loads(jsonified_df)
        oct4_max = df_filename["oct4_max"]
    oct4_slider = dcc.Slider(id='OCT4_low',
                             min=0,
                             max=oct4_max,
                             marks={0: "0", oct4_max: str(oct4_max)},
                             tooltip={"placement": "bottom", "always_visible": True},
                             value=round(oct4_max / 2, 1))
    return oct4_slider


@app.callback(Output('SOX17-slider', 'children'),
              Input('intermediate-value', 'data')
              )
def create_sox17_slider(jsonified_df):
    if jsonified_df is None:
        sox17_max = 5
    else:
        df_filename = json.loads(jsonified_df)
        sox17_max = df_filename["sox17_max"]
    sox17_slider = dcc.Slider(id='SOX17_low',
                              min=0,
                              max=sox17_max,
                              marks={0: "0", sox17_max: str(sox17_max)},
                              tooltip={"placement": "bottom", "always_visible": True},
                              value=round(sox17_max / 2, 1))
    return sox17_slider


@app.callback(
    [Output('heatmap-fig', 'figure'),
     Output('heatmap_pct-fig', 'figure'),
     Output('filter-description', 'children')],
    [Input('intermediate-value', 'data'),
     Input('OCT4_low', 'value'),
     Input('SOX17_low', 'value')]
)
def heatmap(jsonified_df, oct4_low, sox17_low, request):
    if jsonified_df is None or oct4_low is None or sox17_low is None:
        return no_update
    #
    # request.session["celldash"]
    
    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    
    labels = df_filename['labels']
    
    # Heatmap counts
    well_count_matrix_complete = get_well_count_matrix(df=df)
    
    base_label_text = [
        [f"Row: {labels[0][i]}<br>" \
         f"Col: {labels[1][j]}<br>" \
         f"Cell: {labels[2][len(labels[1]) * i + j]}"
         for j in range(len(labels[1]))
         ] for i in range(len(labels[0]))
    ]
    
    label_text = [
        [col+ f"<br>Value: {well_count_matrix_complete.iloc[i, j]}"
            for j, col in enumerate(row)
        ]
        for i, row in enumerate(base_label_text)
    ]
    """
    It is required to invert everything related to the y column, as go.heatmap works from bottom to top.
    There might be a smoother way to solve this but I was not able to find one.
    """
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=np.where(well_count_matrix_complete == 0, None, well_count_matrix_complete)[::-1],
        x=labels[1],
        y=labels[0][::-1],
        hoverinfo='text',
        text=label_text[::-1],
        texttemplate="%{z}",
    ))
    
    filter_description = f"Double positive cells have intensity levels above \
        {sox17_low} for {df.columns[3]} and {oct4_low} for {df.columns[4]}"
    
    # Heatmap percent
    matrix_well_counts = get_well_count_matrix(df,
                                               oct4_low=oct4_low,
                                               sox17_low=sox17_low)
    well_count_matrix_percent = 100 * matrix_well_counts / \
                                well_count_matrix_complete
    
    pct_label_text = [
        [col+ f"<br>Value: {well_count_matrix_percent.iloc[i, j]:.2f}"
            for j, col in enumerate(row)
        ]
        for i, row in enumerate(base_label_text)
    ]
    
    heatmap_pct_fig = go.Figure(data=go.Heatmap(
        z=np.where(well_count_matrix_percent == 0, None, well_count_matrix_percent)[::-1],
        x=labels[1],
        y=labels[0][::-1],
        hoverinfo='text',
        text=pct_label_text[::-1],
        texttemplate="%{z}",
    ))

    return heatmap_fig, heatmap_pct_fig, filter_description


def get_well_count_matrix(df, oct4_low=0, sox17_low=0):
    """
    Returns a cell count matrix representing the cell counts in
    each well in the physical plate where cells are grown. Input data
    frame is filtered on minimum threshholds of oct4 and sox17
    """
    df = df[(df[df.columns[3]] > oct4_low) & (df[df.columns[4]] > sox17_low)]
    well_counts = pd.DataFrame(df["Well"].value_counts())

    well_ids = well_counts.index.to_list()
    well_counts["row"] = [well[0] for well in well_ids]
    well_counts["cols"] = [well[1:] for well in well_ids]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)

    return matrix_well_counts
