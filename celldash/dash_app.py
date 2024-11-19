from dash import Dash, dcc, html, dash_table, Input, Output, State, \
    callback, no_update
import dash_bootstrap_components as dbc
from celldash.callbacks.callbacks import *
from pathlib import Path
import uuid
import pprint
import os
import shutil
import dash_uploader as du
import pandas as pd
from django_plotly_dash import DjangoDash


def emtpy_dir(folder):
    """Remove all files from a folder"""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_upload_component(id):
    emtpy_dir(UPlOAD_FOLDER_ROOT)
    return du.Upload(
        id=id,
        max_file_size=3800,  # in Mb
        filetypes=['csv', 'gz'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


app.layout = html.Div([
    html.Button("get plots??", id="uploaded", n_clicks=0),
    html.Div(id='callback-output'),
    html.H2('Histograms of OCT4 and SOX17 intensity values'),
    dbc.Row(
        [
            # Hist A
            dbc.Col(
                dcc.Graph(id='histogram-plot-a'),
                width=width_histogram
            ),
            # Hist B
            dbc.Col(
                dcc.Graph(id='histogram-plot-b'),
                width=width_histogram
            ),
        ]
    ),
    dbc.Row(
        [
            dbc.Col(
                    # Slider to select OCT4 lower limit
                    [html.H2('Select OCT4 min'),
                    html.Br(),
                    html.Div(id='OCT4-slider')],
                    width=width_histogram),
            dbc.Col(
                    # Slider to select SOX17 lower limit
                    [html.H2('Select SOX17 min'),
                    html.Br(),
                    html.Div(id='SOX17-slider')],
                    width=width_histogram)
        ]
    ),
    # Heatmap cell counts
    html.Br(),
    html.H2('Heatmap of total cell counts per well'),
    dcc.Graph(id='heatmap-fig'),

    # Heatmap percent cells double positive
    html.Br(),
    html.H2('Heatmap of percentage of double positive cell counts \
            per well'),
    html.P("""The percentage of cells that are double positive
           (SOX17 and OCT4 above the set threshold)"""),
    html.Div(id='filter-description'),
    dcc.Graph(id='heatmap_pct-fig'),
    
    dcc.Interval(id='interval-component', interval=1, n_intervals=0),

    # dcc.Store stores the intermediate value
    dcc.Store(id='intermediate-value'),
])



if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)