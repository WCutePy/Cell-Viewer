from functools import reduce

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
    
    def generate_filtered_polars_dataframe(self) -> pl.DataFrame:
        """
        Generates a polars DataFrame applying the filters of each
        threshold.
        
        If the filters are all zero it will skip the filtering step.
        
        The lower threshold is inclusive.
        Returns: pl.DataFrame

        """
        file = self.saved_file.file
        
        data = pl.read_csv(file)
        
        substance_thresholds = self.get_substance_thresholds_as_list
        
        if any(i != 0 for i in substance_thresholds):
            conditions = []
            for i, val in enumerate(substance_thresholds):
                col_name = data.columns[i + 3]
                conditions.append(pl.col(col_name) >= val)
            combined_conditions = reduce(lambda a, b: a & b, conditions)
            data = data.filter(combined_conditions)
        return data
    