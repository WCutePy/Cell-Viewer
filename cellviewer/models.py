from django.db import models
from django.contrib.auth.models import User
from time import time
import polars as pl


# Create your models here.


def file_path(instance, filename) -> str:
    return f"saved_job/{instance.user.id}/{filename}_{int(time())}"


def file_dimensions(file: "InMemoryUploadedFile") -> tuple[int, str]:
    df = pl.read_csv(file)
    rows = df.height
    name = df.columns[0]
    # unique_letters = df[name].str.extract(r"([A-Za-z]+)", 1).unique().height
    # unique_numbers = df[name].str.extract(r"(\d+)", 1).unique().height
    #
    # dimension = f"{unique_letters}x{unique_numbers}"
    dimension = "axb"
    return rows, dimension


class SavedJobManager(models.Manager):
    def create(self, request, file: "InMemoryUploadedFile"):
        
        row_count, dimension = file_dimensions(file)
        
        saved = super().create(
            user_id=request.user.id,
            name="test",
            file=file,
            row_count=row_count,
            dimension=dimension,
        )
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
    