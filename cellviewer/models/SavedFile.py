import os
import sys
from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
from time import time
import polars as pl

from cellviewer.models import file_path
from cellviewer.models.LabelMatrix import LabelMatrix

import hashlib


# Create your models here.


def file_dimensions(df: pl.DataFrame) -> tuple[int, tuple[list[str], list[str]]]:
    """
    Helper function which returns the row count, and all row names and
    column names that appear as a sorted list, to have the dimensions
    be calculated from that.
    It presumes all the letters it can find are the rows.
    All the numbers are the columns. It does not care
    if a letter number combination is missing and ignores such things.
    Args:
        df:

    Returns:

    """
    rows = df.height
    name = df.columns[0]
    tags = df[name].arr.explode().unique().to_list()
    
    letters = sorted(set(t.strip(digits) for t in tags))
    numbers = sorted(set(t.strip(ascii_letters) for t in tags))
    return rows, (letters, numbers)


class SavedFileManager(models.Manager):
    def create(self, request, file: "InMemoryUploadedFile"):
        file_hash = hashlib.file_digest(file, 'sha256').hexdigest()
        file_with_hash = self.find_equivalent(file_hash)
        if file_with_hash is not None:
            return file_with_hash
        
        file.open()
        df = pl.read_csv(file)
        
        row_count, dimension = file_dimensions(df)
        matrix_row_count, matrix_col_count = len(dimension[0]), len(dimension[1])
        dimension = f"{matrix_row_count}x{matrix_col_count}"
        
        saved = super().create(
            user_id=request.user.id,
            file=file,
            row_count=row_count,
            matrix_row_count=matrix_row_count,
            matrix_col_count=matrix_col_count,
            dimension=dimension,
            
            hash=file_hash
        )
        
        saved.save()
        return saved
    
    def get_all_for_user(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        return self.filter(user_id=user)
    
    def find_equivalent(self, file_hash: str) -> "SavedFile":
        return self.filter(
            hash=file_hash
        ).first()


class SavedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=file_path)
    row_count = models.IntegerField()
    matrix_row_count = models.IntegerField()
    matrix_col_count = models.IntegerField()
    
    dimension = models.CharField(max_length=100)
    
    hash = models.TextField()
    
    date = models.DateTimeField(auto_now_add=True)
    
    objects = SavedFileManager()
    
    def delete(self, *args, **kwargs):
        if self.job_files.all().exists():
            return
            
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        else:
            pass
        return super().delete(*args, **kwargs)