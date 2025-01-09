from functools import reduce

import pandas as pd
import polars as pl
from django.db import models

from apps.cellviewer.models.SavedJob import SavedJob
from apps.cellviewer.models.SavedFile import SavedFile


class FilteredFile(models.Model):
    """
    An inbetween table between the job and a saved file.
    A filtered file simply holds additional data that is
    relevant to the connection between the two.
    
    In certain cases if both the job and saved file are needed,
    it is better to query for the tables through the filteredFile,
    this reduces the amount of queries required.
    This can be done with the code:
        FilteredFile.objects.filter(job_id__in=job_ids).select_related \
        ('job', 'saved_file')
        
    This table has been created because it was originally intended for a
    job / experiment to have multiple files assigned to it.
    The substance_thresholds as filter can be applied
    differently to each file.
    
    This is currently used as an interface for methods
    that use an individual file.
    
    """
    
    job = models.ForeignKey(SavedJob, on_delete=models.CASCADE)
    saved_file = models.ForeignKey(SavedFile, on_delete=models.CASCADE)
    substance_thresholds = models.TextField(null=True, default=None)
    
    @property
    def get_substance_thresholds_as_list(self) -> list[float]:
        """
        Converts the substance thresholds to a list of floats
        Returns: list[float]

        """
        return [float(i) for i in
                self.substance_thresholds.split(";")]
    
    def load_polars_dataframe(self) -> pl.DataFrame:
        file = self.saved_file.file
        
        return pl.read_csv(file)
    
    def generate_filtered_polars_dataframe(self, df=None) -> pl.DataFrame:
        """
        Generates a polars DataFrame applying the filters of each
        threshold.
        
        If the filters are all zero it will skip the filtering step.
        
        The lower threshold is inclusive.
        Returns: pl.DataFrame

        """
        if df is None:
            df = self.load_polars_dataframe()
        
        substance_thresholds = self.get_substance_thresholds_as_list
        
        if any(i != 0 for i in substance_thresholds):
            conditions = []
            for i, val in enumerate(substance_thresholds):
                col_name = df.columns[i + 3]
                conditions.append(pl.col(col_name) >= val)
            combined_conditions = reduce(lambda a, b: a & b, conditions)
            df = df.filter(combined_conditions)
        return df
    
    def generate_well_count_matrix(self, df=None):
        """
        Returns a cell count matrix representing the cell counts in
        each well in the physical plate where cells are grown.
        """
        if df is None:
            df = self.load_polars_dataframe()
        
        well_counts = df.group_by("Well").count().to_pandas()

        well_counts["row"] = [well[0] for well in well_counts["Well"]]
        well_counts["cols"] = [well[1:] for well in well_counts["Well"]]
        matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                               values="count")
        matrix_well_counts.fillna(0, inplace=True)

        return matrix_well_counts
    
    @staticmethod
    def generate_well_count_percent(well_count_matrix, filtered_well_count_matrix):
        return (100 * filtered_well_count_matrix / well_count_matrix).fillna(0)
    
    def get_well_count_and_well_count_percent(self):
        df = self.load_polars_dataframe()
        
        df_filtered = self.generate_filtered_polars_dataframe(df)
        
        well_count_matrix = self.generate_well_count_matrix(df)
        
        filtered_well_count_matrix = self.generate_well_count_matrix(
            df_filtered)
        
        well_count_matrix_percent = self.generate_well_count_percent(
            well_count_matrix, filtered_well_count_matrix)
        
        return well_count_matrix, well_count_matrix_percent