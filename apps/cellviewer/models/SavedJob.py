from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
import polars as pl

from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.models.SavedFile import SavedFile
from django.db import transaction


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
    
    @transaction.atomic
    def create(self, request, files: list["InMemoryUploadedFile"], name: str, labels: tuple[tuple[str]], label_matrix_name: str):
        """
        Saves a "job" in the database. This manages the creation of all aspects of it.
        
        The related aspects:
            Itself
            The files which are stored in SavedFile
            The LabelMatrix
        
        The create is atomic to ensure that if anything goes wrong,
        all changes will be reverted. This however does not revert
        the saving of files to disk using FileField.
        It is thereby possible for an orphaned file to occur.
        Currently nothing is robustly in place
        to ensure these do not occur. This would require an aggresive
        check after each create when an error occurs,
        or a scheduled cronjob.
        Currently the saving of the files to disk is delayed as far
        as possible until .save() is called.
        is called on the SavedFile objects, the chance for an orphan
        to occur is minimalized.
        In theory this should only be possible with an unexpected
        crash or forced shutdown of the system.
        
        There are multiple checks and errors the create can throw.
        
        If the files have different dimensions from each other
        a ValueError will be raised. This will cancel the creation.
        
        If the files and LabelMatrix have different dimensions
        from each other a ValueError will be raised.
        This will cancel the creation. It is not known if users
        can trigger this error through intended use.
        
        SavedFile throws a PermissionError if there is not enough
        space available to the user to write the file.
        
        Currently, any creates that happen in the middle if an error is raised remain
        There will be objects created that are "orphaned"
        Args:
            label_matrix_name:
            request:
            files:
            name:
            labels:

        Returns:

        """
        to_save_files = []
        first_dimension, next_dimension = (0, 0), (0, 0)
        
        current_users_size_in_b = SavedJob.objects.get_users_used_file_storage(request.user)
        
        for file in files:
            initialized_file_object, current_users_size_in_b = SavedFile.create(request, file, current_users_size_in_b)
            
            next_dimension = (initialized_file_object.matrix_row_count, initialized_file_object.matrix_col_count)
            if next_dimension != first_dimension and first_dimension != (0, 0):
                raise ValueError(f"DataFrames have different shapes\n"
                                 f"first_dimension: {first_dimension}\n"
                                 f"next_dimension: {next_dimension}"
                                 )
            
            if (len(labels[0]), len(labels[1])) != next_dimension:
                raise ValueError(f"The label and file content dimension does not match\ndimensions:"
                                 f"label: {(len(labels[0]), len(labels[1]))}\n"
                                 f"dimension: {first_dimension}"
                                 )
            
            first_dimension = next_dimension
            to_save_files.append(initialized_file_object)

        if not label_matrix_name and name:
            label_matrix_name = f"{name}_annotation"
        label_matrix = LabelMatrix.objects.create(request, *labels, label_matrix_name)
        
        saved_job = super().create(
            user_id=request.user.id,
            name=name,
            dimension=to_save_files[0].dimension,
            label_matrix=label_matrix
        )
        
        if not name:
            saved_job.name = f"job-{saved_job.id}"
        
        saved_job.save()
        
        for file in to_save_files:
            file.save()
        saved_job.files.add(*to_save_files)
        
        return saved_job
    
    def get_all_jobs_for_user(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        return self.filter(user_id=user)
    
    def get_users_used_file_storage(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        unique_files = self.filter(user_id=user).values("files").distinct()
        storage = SavedFile.objects.filter(id__in=unique_files) \
            .aggregate(models.Sum("storage_space_in_b"))["storage_space_in_b__sum"]
        if storage is None:
            storage = 0
        return storage


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    
    files = models.ManyToManyField(SavedFile, related_name="job_files")
    
    date = models.DateTimeField(auto_now_add=True)
    
    dimension = models.CharField(max_length=100)
    label_matrix = models.ForeignKey(LabelMatrix, on_delete=models.SET_NULL,
                                     related_name="job_label", null=True)
    
    objects = SavedJobManager()
    
    def delete(self, *args, **kwargs):
        for saved_file in self.files.all():
            self.files.remove(saved_file)
            saved_file.delete()
        
        self.label_matrix.delete()
        
        return super().delete(*args, **kwargs)
