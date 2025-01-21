import pandas as pd
import polars as pl
from functools import reduce


def filtered_polars_dataframe(df: pl.DataFrame,
                              substance_thresholds: list[float]):
    if any(i != 0 for i in substance_thresholds):
        conditions = []
        for i, val in enumerate(substance_thresholds):
            col_name = df.columns[i + 3]
            conditions.append(pl.col(col_name) >= val)
        combined_conditions = reduce(lambda a, b: a & b, conditions)
        df = df.filter(combined_conditions)
    return df


def generate_well_count_matrix(df: pl.DataFrame) -> pd.DataFrame:
    well_counts = df.group_by("Well").count().to_pandas()
    
    well_counts["row"] = [well[0] for well in well_counts["Well"]]
    well_counts["cols"] = [well[1:] for well in well_counts["Well"]]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    
    return matrix_well_counts


def generate_well_count_percent(well_count_matrix, filtered_well_count_matrix):
    return round((100 * filtered_well_count_matrix / well_count_matrix),1).fillna(0)


def generate_well_counts_and_percent(df, substance_thresholds):
    df_filtered = filtered_polars_dataframe(
        df, substance_thresholds
    )
    
    well_count_matrix = generate_well_count_matrix(df)
    
    filtered_well_count_matrix = generate_well_count_matrix(
        df_filtered
    )
    
    well_count_matrix_percent = generate_well_count_percent(
        well_count_matrix, filtered_well_count_matrix)
    
    return (well_count_matrix, filtered_well_count_matrix,
            well_count_matrix_percent)
