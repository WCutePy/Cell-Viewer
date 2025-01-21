from string import digits, ascii_letters

from django.db import models
from django.contrib.auth.models import User
import polars as pl

from django.db.models import QuerySet
from apps.cellviewer.models.LabelMatrix import LabelMatrix
from apps.cellviewer.models.SavedFile import SavedFile
from django.db import transaction
from django.apps import apps


class SavedJobManager(models.Manager):
    
    @transaction.atomic
    def create(
            self, request, files: list["InMemoryUploadedFile"],
            files_substance_thresholds,
            name: str, labels: tuple[tuple[str]], label_matrix_name: str):
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
            files_substance_thresholds:
            name:
            labels:

        Returns:

        """
        to_save_files = []
        first_dimension, next_dimension = (0, 0), (0, 0)
        
        current_users_size_in_b = SavedJob.objects.get_users_used_file_storage(request.user)
        
        for file in files:
            initialized_file_object, current_users_size_in_b = (
                SavedFile.objects.create(request, file, current_users_size_in_b)
            )
            
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
        
        if label_matrix.matrix_name == "Annotation name":
            label_matrix.matrix_name = f"Annotation {saved_job.name}"
            label_matrix.save()
        
        FilteredFile = apps.get_model("cellviewer", "FilteredFile")
        
        for file, file_instance, substance_thresholds in zip(files, to_save_files, files_substance_thresholds):
            file_instance.save()
            
            filtered_file = FilteredFile.objects.create(
                job=saved_job,
                saved_file=file_instance,
                created_by_id=request.user.id,
                original_file_name=file.name,
                substance_thresholds=";".join(str(i) for i in substance_thresholds),
            )
            filtered_file.save()
            
        # saved_job.files.add(*to_save_files)
        
        return saved_job
    
    def get_all_jobs_for_user(self, user: User | int) -> QuerySet:
        """
        Gets all jobs of a certain user, by their User object
        or the user id
        Args:
            user:

        Returns: Queryset
        """
        if isinstance(user, User):
            user = user.id
        return self.filter(user_id=user)
    
    def get_all_viewable_jobs(self, user: User | int) -> QuerySet:
        """
        All viewable jobs might be changed in the future.
        Currently this constitutes all jobs in the database.
        Returns:

        """
        return self.all()
        
    def get_users_used_file_storage(self, user: User | int) -> int:
        """
        Determines an estimation of a users used file storage in bytes.
        by summing the size recorded into the database of
        each unique file.
        
        It is likely for the actual size to exceed this number
        related to the way the operating system writes to disk.
        However this is expected to be a small difference
        and not be significantly impactful.
        
        Args:
            user: User object or user id

        Returns: Used file storage in bytes

        """
        if isinstance(user, User):
            user = user.id
        unique_files = self.filter(user_id=user).values("files").distinct()
        storage = SavedFile.objects.filter(id__in=unique_files) \
            .aggregate(models.Sum("storage_space_in_b"))["storage_space_in_b__sum"]
        if storage is None:
            storage = 0
        return storage


class SavedJob(models.Model):
    """
    A SavedJob/experiment
    
    A SavedJob/experiment can have multiple files assigned to it
    with the same dimension, and has a label matrix with the
    same dimensions
    
    Everything to do with a single experiment should
    be handled from a SavedJob.
    
    Currently adding multiple files to one SavedJob
    is not done/supported within the whole application,
    so using multiple SavedJob's might be done.
    Doing things that way is a workaround and not the originally
    intended design. However if it works it works.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    
    files = models.ManyToManyField(
        SavedFile, related_name="job_files",
        through="FilteredFile"
    )
    
    date = models.DateTimeField(auto_now_add=True)
    
    dimension = models.CharField(max_length=100)
    label_matrix = models.ForeignKey(LabelMatrix, on_delete=models.SET_NULL,
                                     related_name="job_label", null=True)
    
    objects = SavedJobManager()
    
    def delete(self, *args, **kwargs):
        """
        Deletes a SavedJob
        
        For each file it will remove them from the SavedJob and
        then attempt to delete them. It is possible this will
        fail as other SavedJobs still reference the file.
        This will fail silently.
        It is required that the file is removed from the SavedJob.
        If not the super().delete() will force remove it anyways.
        
        It attempts to delete the LabelMatrix.
        This too fails silently if it is referenced by other
        SavedJobs.
        
        Args:
            *args:
            **kwargs:

        Returns:

        """
        for saved_file in self.files.all():
            self.files.remove(saved_file)
            saved_file.delete()
        
        self.label_matrix.delete()
        
        return super().delete(*args, **kwargs)
    
    def is_viewable_by(self, user: int | User):
        """
        Currently the request is that everything is viewable for
        everyone. As such, this function is a placeholder
        for more complex future logic.
        
        If this logic never comes that is fine, however
        it is better to keep it in mind, rather than
        delete any checking that previously existed already.
        Args:
            user:

        Returns:

        """
        if isinstance(user, User):
            user = user.id
        
        return True
    
    def is_deletable_by(self, user: int | User):
        """
        This too moves the check to a class based existence.
        
        Args:
            user:

        Returns:

        """
        if isinstance(user, User):
            user = user.id
        
        return self.user.id == user
    