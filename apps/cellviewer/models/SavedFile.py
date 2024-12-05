import os
import sys
from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
from time import time, strftime
import polars as pl

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


def saved_file_path_func(instance, filename) -> str:
    return strftime(f"saved_files/%Y/%m/{filename}_{int(time())}")


class SavedFileManager(models.Manager):
    
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
    file = models.FileField(upload_to=saved_file_path_func)
    storage_space_in_b = models.IntegerField()
    row_count = models.IntegerField()
    
    matrix_row_count = models.IntegerField()
    matrix_col_count = models.IntegerField()
    dimension = models.CharField(max_length=100)
    
    hash = models.TextField()
    
    date = models.DateTimeField(auto_now_add=True)
    
    objects = SavedFileManager()
    
    @classmethod
    def create(cls, request, file: "InMemoryUploadedFile", current_users_size=None):
        """
        Creates an instance of SavedFile. This instance does not hit the database
        until it is stored with .save()
        
        When creating objects for SavedFile, if it's possible it might
        need to be reverted, one should always use this method.
        
        SavedFiles are hashed, to check if a file already exists
        in the database. If a file that's being created already
        exists, it will not be saved again and no new instance
        will be created. Instead it silently returns the prior
        saved SavedFile object. This is done to save space.
        
        It will check if saving the file to disk will exceed
        the users remaining available storage space.
        If it would exceed it an PermissionError is thrown.
        It is possible to pass the current used size as variable,
        if this is not done it will query this information on it's own.
        To avoid circular imports, it will import the necessary function
        for this.
        
        Besides this it calculates the simple information about
        the file.
        
        Args:
            request:
            file:
            current_users_size:

        Returns:
            The newly saved, or cached file.
            The current users size after saving the file.
        """
        file_hash = hashlib.file_digest(file, 'sha256').hexdigest()
        file_with_hash = cls.objects.find_equivalent(file_hash)
        if file_with_hash is not None:
            return file_with_hash, current_users_size
        
        if current_users_size is None:
            from apps.cellviewer.models.SavedJob import SavedJob
            current_users_size = SavedJob.objects.get_users_used_file_storage(request.user)
        
        new_size = current_users_size + file.size
        if new_size > (request.user.profile.storage_space_in_gb * 1000000000):
            raise PermissionError("Not enough space to write more files")
        
        file.open()
        df = pl.read_csv(file)
        
        row_count, dimension = file_dimensions(df)
        matrix_row_count, matrix_col_count = len(dimension[0]), len(dimension[1])
        dimension = f"{matrix_row_count}x{matrix_col_count}"
        
        instance = cls(
            user_id=request.user.id,
            file=file,
            storage_space_in_b=file.size,
            row_count=row_count,
            matrix_row_count=matrix_row_count,
            matrix_col_count=matrix_col_count,
            dimension=dimension,
            
            hash=file_hash
        )

        return instance, new_size
    
    @classmethod
    def delete_by_file_path(cls, file_path):
        """
        Handles the deletion of an individual file.
        
        Currently, nothing is implemented to handle
        the failure to delete a file as a part of this function.
        It makes the assumption that the attempt to delete a file
        will always succeed on Unix based operating systems.
        Args:
            file_path:

        Returns:

        """
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError
    
    def delete(self, *args, **kwargs):
        if self.job_files.all().exists():
            return
            
        self.delete_by_file_path(self.file.path)
        return super().delete(*args, **kwargs)