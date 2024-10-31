from pathlib import Path
from io import StringIO
import plotly.express as px


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


def create_all_hist_html(df, columns):
    hists = []
    for column in columns:
        hist = create_hist(df, column)
        html = hist.to_json()
        hists.append(html)
    return hists
