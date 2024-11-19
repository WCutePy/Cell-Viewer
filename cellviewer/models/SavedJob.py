import os
from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
from time import time
import polars as pl

from cellviewer.models import file_path
from cellviewer.models.LabelMatrix import LabelMatrix


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


class SavedJobManager(models.Manager):
    def create(self, request, file: "InMemoryUploadedFile", name: str, labels: tuple[tuple[str]]):
        df = pl.read_csv(file)
        
        row_count, dimension = file_dimensions(df)
        dimension = f"{len(dimension[0])}x{len(dimension[1])}"
        
        label_matrix_id = LabelMatrix.objects.create(request, *labels)
        
        saved = super().create(
            user_id=request.user.id,
            name=name,
            file=file,
            row_count=row_count,
            dimension=dimension,
            label_matrix=label_matrix_id
        )
        
        if not name:
            saved.name = f"job-{saved.id}"
        
        saved.save()
        return saved
    
    def get_all_jobs_for_user(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        return self.filter(user_id=user)


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=file_path)
    date = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField()
    dimension = models.CharField(max_length=100)
    
    label_matrix = models.ForeignKey(LabelMatrix, on_delete=models.PROTECT)
    
    objects = SavedJobManager()
    
    def delete(self, *args, **kwargs):
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        
        return super().delete(*args, **kwargs)