from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
import polars as pl

from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.models.SavedFile import SavedFile


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
    def create(self, request, files: list["InMemoryUploadedFile"], name: str, labels: tuple[tuple[str]]):
        saved_files = []
        first_dimension, next_dimension = (0, 0), (0, 0)
        for file in files:
            saved_file = SavedFile.objects.create(request, file)
            
            next_dimension = (saved_file.matrix_row_count, saved_file.matrix_col_count)
            if next_dimension != first_dimension and first_dimension != (0, 0):
                raise ValueError(f"DataFrames have different shapes\n"
                                 f"first_dimension: {first_dimension}\n"
                                 f"next_dimension: {next_dimension}"
                                 )
            first_dimension = next_dimension
            saved_files.append(saved_file)
        
        if (len(labels[0]), len(labels[1])) != first_dimension:
            raise ValueError(f"The label and file content dimension does not match\ndimensions:"
                             f"label: {(len(labels[0]), len(labels[1]))}\n"
                             f"dimension: {first_dimension}"
                             )
        label_matrix = LabelMatrix.objects.create(request, *labels)
        
        saved = super().create(
            user_id=request.user.id,
            name=name,
            dimension=saved_files[0].dimension,
            label_matrix=label_matrix
        )
        saved.files.add(*saved_files)
        
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
    
    files = models.ManyToManyField(SavedFile, related_name='job_files')
    
    date = models.DateTimeField(auto_now_add=True)

    dimension = models.CharField(max_length=100)
    label_matrix = models.ForeignKey(LabelMatrix, on_delete=models.PROTECT)
    
    objects = SavedJobManager()
    
    def delete(self, *args, **kwargs):
        
        for saved_file in self.files.all():
            print(saved_file.id)
            self.files.remove(saved_file)
            saved_file.delete()
        
        return super().delete(*args, **kwargs)
        