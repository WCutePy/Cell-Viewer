import pandas as pd
import polars as pl
from functools import reduce


def filtered_polars_dataframe(
        df: pl.DataFrame, substance_thresholds: list[float]
) -> pl.DataFrame:
    """
    Filters out rows that have a lower value than any of the thresholds.
    This means that the threshold is INCLUSIVE. If the threshold is
    2, a value of 2 will be retained, and 1.99 will be filtered out.
    
    This function currently just loops over the thresholds to
    create the filter. If there are less thresholds than the
    amount of different substances in the dataset, it will filter
    on the first n substances.
    If there are more it will fail.
    
    Args:
        df:
        substance_thresholds:

    Returns:

    """
    if any(i != 0 for i in substance_thresholds):
        conditions = []
        for i, val in enumerate(substance_thresholds):
            col_name = df.columns[i + 3]
            conditions.append(pl.col(col_name) >= val)
        combined_conditions = reduce(lambda a, b: a & b, conditions)
        df = df.filter(combined_conditions)
    return df


def calculate_well_count_matrix(df: pl.DataFrame) -> pd.DataFrame:
    """
    Calculates the well count matrix.
    
    It expects a polars DataFrame, and returns a pandas DataFrame.
    This can be a bit confusing.
    
    This is done because polars, to my knowledge, when it comes
    to loading and this type of operation is a bit faster than
    pandas. (More testing would be needed to proof if this is
    consistently true for the current Pandas version)
    However Polars does not play nice with the matrix format
    that is required to be used for the application.
    
    As such this conversion is made after the heavy lifting has
    been done by Polars.
    
    It creates a Matrix in the format:
    
    cols  02  03
    row
    B      1   0
    C      0   1
    
    It makes every combination of all letters and numbers that appear.
    Well combinations that are missing, will be defaulted to zero.
    
    Args:
        df:

    Returns:

    """
    well_counts = df.group_by("Well").count().to_pandas()
    
    well_counts["row"] = [well[0] for well in well_counts["Well"]]
    well_counts["cols"] = [well[1:] for well in well_counts["Well"]]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    
    return matrix_well_counts


def calculate_well_count_percent(well_count_matrix, filtered_well_count_matrix):
    """
    Calculates the percentage of two well count matrices.
    
    It is not required for the matrices to be the exact same shape,
    however it is intended for this to be the case.
    
    Percentages are between 0 and 100 %
    Any values that are missing, or NaN, will be filled to zero, as it
    might complicate other calculations relying on this data
    if they are NaN.
    
    Args:
        well_count_matrix:
        filtered_well_count_matrix:

    Returns:

    """
    return (100 * filtered_well_count_matrix / well_count_matrix).fillna(0)


def calculate_well_counts_and_percent(df, substance_thresholds):
    """
    Gets the well count, filtered well count and double positive
    percentage all from a singular function call, wrapping together
    multiple functions from this file.
    
    A note is that, it's possible in some cases for the filtering
    to filter out for example all Wells with the letter B,
    In that case calculating the well count would not have
    wells with the letter B appear at all.
    The original well count matrix is used to adjust for this,
    so no Well combinations can be missed in the output.
    
    This could be made into a separate function,
    however it's not intended to do anything without this combined
    function, so that might not be necessary.
    
    Args:
        df:
        substance_thresholds:

    Returns:

    """
    df_filtered = filtered_polars_dataframe(
        df, substance_thresholds
    )
    
    well_count_matrix = calculate_well_count_matrix(df)
    
    filtered_well_count_matrix = calculate_well_count_matrix(
        df_filtered
    ).reindex(index=well_count_matrix.index, columns=well_count_matrix.columns, fill_value=0)
    
    well_count_matrix_percent = calculate_well_count_percent(
        well_count_matrix, filtered_well_count_matrix)
    
    return (well_count_matrix, filtered_well_count_matrix,
            well_count_matrix_percent)


def calculate_mean_across_each_well(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Calculates the mean across each well given a list of pandas dataframes
    in a matrix like configuration.
    
    It returns a matrix of the same dimension as the first matrix
    where each well is the mean of all values of that well.
    
    Example:
    Given the two matrices the expected outcome is matrix Result
    Matrix A
        1   2
    A   20  40
    B   60  80
    
    Matrix B
        1   2
    A   30  50
    B   -10 10
    
    Result
        1   2
    A   25  45
    B   25  45
    
    Args:
        dfs: A list of pandas Dataframes

    Returns: A pandas Dataframe
    """
    mean_matrix = pd.DataFrame(0, index=dfs[0].index,
                               columns=dfs[0].columns)
    
    for df in dfs:
        mean_matrix += df
    
    mean_matrix /= len(dfs)
    return mean_matrix
    

def calculate_standard_deviation_across_each_well(
        dfs: list[pd.DataFrame], mean_df: pd.DataFrame) -> (pd.DataFrame):
    """
    This makes use of the formula for discrete random
    variable.
    
    Calculates the standard deviation across each well given a
    list of pandas dataframes in a matrix like configuration.
    
    It returns a matrix of the same dimension as the first matrix
    where each well is the standard deviation of all values of that well.
    
    if the size is smaller than 30, it will use the formula with
    n - 1
    
    Args:
        dfs:

    Returns:

    """
    std_matrix = pd.DataFrame(0, index=dfs[0].index,
                              columns=dfs[0].columns)
    
    for df in dfs:
        std_matrix += (df - mean_df) ** 2
    
    n = len(dfs)
    if n < 30:
        n = n - 1
    std_matrix = (std_matrix / n) ** 0.5
    return std_matrix
