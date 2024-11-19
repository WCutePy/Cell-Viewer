import os
from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
from time import time
import polars as pl


# Create your models here.


def file_path(instance, filename) -> str:
    return f"saved_job/{instance.user.id}/{filename}_{int(time())}"


def file_dimensions(df: pl.DataFrame) -> tuple[int, tuple[list[str], list[str]]]:
    rows = df.height
    name = df.columns[0]
    tags = df[name].arr.explode().unique().to_list()
    
    letters = sorted(set(t.strip(digits) for t in tags))
    numbers = sorted(set(t.strip(ascii_letters) for t in tags))
    return rows, (letters, numbers)


class SavedJobManager(models.Manager):
    def create(self, request, file: "InMemoryUploadedFile", name: str):
        df = pl.read_csv(file)
        
        row_count, dimension = file_dimensions(df)
        dimension = f"{len(dimension[0])}x{len(dimension[1])}"
        
        saved = super().create(
            user_id=request.user.id,
            name=name,
            file=file,
            row_count=row_count,
            dimension=dimension,
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
    
    objects = SavedJobManager()
    
    def delete(self, *args, **kwargs):
        
        if os.path.isfile(self.file.path):
            os.remove(self.file.path)
        
        return super().delete(*args, **kwargs)