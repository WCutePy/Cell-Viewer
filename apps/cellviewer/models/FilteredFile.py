from functools import reduce

import pandas as pd
import polars as pl
from django.contrib.auth.models import User
from django.db import models

from apps.cellviewer.models.SavedJob import SavedJob
from apps.cellviewer.models.SavedFile import SavedFile
from apps.cellviewer.util.matrix_functions import \
    calculate_well_counts_and_percent


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
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    original_file_name = models.TextField(null=True, default=None)
    substance_thresholds = models.TextField(null=True, default=None)
    
    @property
    def get_substance_thresholds_as_list(self) -> list[float]:
        """
        Converts the substance thresholds to a list of floats
        
        It's apparently possible that the thresholds are empty strings,
        in that case it will use a threshold of 0 as default, this
        only really happens with unintended usage of the application
        and/or incorrect handling of bad user input, however as
        was noticed that this occurred at this point it was added
        here too as a fix. It would be better if where saving the
        FilteredFile happens covers this case.
        
        
        Returns: list[float]

        """
        return [float(i) if i else 0 for i in
                self.substance_thresholds.split(";")]
    
    def load_polars_dataframe(self) -> pl.DataFrame:
        file = self.saved_file.file
        
        return pl.read_csv(file)
    
    def get_well_counts_and_percent(self, df=None,
                                         substance_thresholds=None):
        if df is None:
            df = self.load_polars_dataframe()
        
        if substance_thresholds is None:
            substance_thresholds = self.get_substance_thresholds_as_list
        
        well_count_matrix, filtered_well_count_matrix, \
            well_count_matrix_percent = \
            calculate_well_counts_and_percent(
                df, substance_thresholds
            )
        
        return well_count_matrix, filtered_well_count_matrix, \
            well_count_matrix_percent
