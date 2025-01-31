import pandas as pd
import polars as pl
from functools import reduce


def filtered_polars_dataframe(
        df: pl.DataFrame, substance_thresholds: list[float]
) -> pl.DataFrame:
    """
    Filters out values that are lower than any of the thresholds.
    This means that the threshold is INCLUDED
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
    well_counts = df.group_by("Well").count().to_pandas()
    
    well_counts["row"] = [well[0] for well in well_counts["Well"]]
    well_counts["cols"] = [well[1:] for well in well_counts["Well"]]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    
    return matrix_well_counts


def calculate_well_count_percent(well_count_matrix, filtered_well_count_matrix):
    return (100 * filtered_well_count_matrix / well_count_matrix).fillna(0)


def calculate_well_counts_and_percent(df, substance_thresholds):
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
    
    Args:
        dfs:

    Returns:

    """
    std_matrix = pd.DataFrame(0, index=dfs[0].index,
                              columns=dfs[0].columns)
    
    for df in dfs:
        std_matrix += (df - mean_df) ** 2
    
    std_matrix = (std_matrix / len(dfs)) ** 0.5
    return std_matrix
