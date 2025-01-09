from typing import Union

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.db.models import QuerySet


class LabelMatrixManager(models.Manager):
    
    @staticmethod
    def joiner(x):
        """a helper function that joins, using the specific character
        used to store the strings to the database.
        """
        return ",,,".join(x)
    
    def create(self, request, rows: tuple[str], cols: tuple[str], cells: tuple[str], label_matrix_name: str, public=False, keep_when_unused=False):
        """
        Creates an instance of a LabelMatrix/AnnotationMatrix.
        
        It will check if an equivalent matrix already exists,
        if this is the case it will not create a new matrix
        and silently return the id of the existing matrix.
        This behaviour would need to be changed if one
        wishes to notify the user of this.
        
        It is currently possible for another user's matrix
        to get returned as long as it is set to public.
        
        If the matrix does get created
        The matrix will be recorded as created by the user in
        the request object.
        
        If no name is passed, it will default to the id of the
        annotation-{id} with id as the row id in the database.
        
        Args:
            request:
            rows:
            cols:
            cells:
            label_matrix_name:
            public:
            keep_when_unused:

        Returns:

        """
        rows_str, cols_str, cells_str = self.joiner(rows), self.joiner(cols), self.joiner \
            (cells)
        
        equivalent = self.find_equivalent(request.user.id, label_matrix_name, len(rows), len(cols), rows_str, cols_str, cells_str)
        if equivalent is not None:
            return equivalent
        
        saved = super().create(
            created_by_id=request.user.id,
            public=public,
            keep_when_unused=keep_when_unused,
            matrix_name=label_matrix_name,
            row_count=len(rows),
            col_count=len(cols),
            rows=rows_str,
            cols=cols_str,
            cells=cells_str,
        )
        
        if not label_matrix_name:
            saved.matrix_name = f"annotation-{saved.id}"
        saved.save()
        return saved
    
    def get_queryset(self):
        """
        Overrides the models.Manager method
        This override is done so a string for the dimension can
        be derived from a queryset, without additionally storing
        it in the database, or touching the database again.
        
        It can be easy to miss that it exists.
        More of these fields can be added in the future if
        that is a preferred solution.
        Be certain that this is required/best for what you are
        trying to do.
        
        This does not affect any of the behaviour of Querysets.
        """
        qs = super(LabelMatrixManager, self).get_queryset().annotate(
            dimension_string=Concat("row_count",Value("x"), 'col_count', output_field=models.TextField())
        )
        return qs
    
    def get_all_of_user(self, user: User | int) -> QuerySet:
        """
        Gets all LabelMatrices belonging to a certain user
        
        Args:
            user: The User or the User id

        Returns: Queryset of all the matrices

        """
        if isinstance(user, User):
            user = user.id
        return self.filter(created_by=user)
    
    def find_equivalent(self, user, label_matrix_name, row_count, col_count, rows_str, cols_str,
                        cells_str) -> Union["LabelMatrix", None]:
        """
        Searches if an equivalent matrix exists.
        It will compare all identifying variables to each other.
        
        It only compares to the own user's matrices and public
        matrices.
        It is possible if two users make the exact same matrix
        with the same name, that user 2 might not be able to
        edit the matrix in the future because it will not
        "belong" to them.
        
        This is used to avoid duplicate copies, and allow
        for changes through one Job/experiment to affect all
        uses of the same matrix.
        
        Find equivalent is intended to only check during creation,
        so through update, two Label Matrices can become identical.
        
        If an attempt to make a "third" is done, this function
        will grab the "first" of the two existing one, defined
        by Django's first method.
        
        Args:
            user:
            label_matrix_name:
            row_count:
            col_count:
            rows_str:
            cols_str:
            cells_str:

        Returns:

        """
        return self.filter(
            Q(created_by=user) | Q(public=True),
            matrix_name=label_matrix_name,
            row_count=row_count,
            col_count=col_count,
            rows=rows_str,
            cols=cols_str,
            cells=cells_str,
            
        ).first()
    
    def get_all_same_size(self, user: User | int, row_count: int, col_count: int) -> QuerySet:
        """
        This will get all available matrices of the same size.
        Currently, any annotation matrix set to public with
        the same size will be shown along their own.
        On a larger userbase this would not be preferred.
        Args:
            user: The user or their id
            row_count: The amount of rows
            col_count: The amount of columns

        Returns: A queryset with all matrices of the same size

        """
        if isinstance(user, User):
            user = user.id
        query = (Q(created_by=user) | Q(public=True)) & \
                 Q(row_count=row_count) & Q(col_count=col_count)
        return self.filter(query)


class LabelMatrix(models.Model):
    """
    The LabelMatrix, also known as the AnnotationMatrix
    (might be best to rename it to this for clarity)
    
    It holds annotation information for rows, columns and cells,
    This annotation is used by a Job/experiment to display (custom)
    information about the content.
    
    A LabelMatrix stores the row names, column names and cell names.
    These are stored in a string as databases do not have variable
    sized lists. The string is split and joined. through methods and
    functions in this file. see joiner, and see get_labels.
    
    It also holds information such as the name of the matrix,
    if it should be visible to other users and if to
    keep it when no jobs/experiments use it.
    
    Currently there is no big sharing mechanism in place, but this
    would allow the LabelMatrix to be shared with all or select
    users if wanted.
    
    The default behaviour expected from a LabelMatrix is
    that it is automatically deleted together with the last Job/experiment
    that makes use of it. As long as any references to it are made
    it will not be deleted.
    This also means that LabelMatrices are expected to be used
    by multiple Jobs/experiments.
    """

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField()
    matrix_name = models.CharField(max_length=255, default="unnamed")
    keep_when_unused = models.BooleanField(default=False)
    
    row_count = models.IntegerField()
    col_count = models.IntegerField()
    rows = models.TextField()
    cols = models.TextField()
    cells = models.TextField()
    
    objects = LabelMatrixManager()
    
    def update(self, rows: tuple[str], cols: tuple[str], cells: tuple[str], label_matrix_name: str, keep_when_unused, public):
        """
        Updates an existing instance with the new values.
        It naively updates every value, even if they are not
        changed.
        
        Args:
            rows: A list of the new row names
            cols: A list of the new column names
            cells: A list of the new cell names
            label_matrix_name: The new label_matrix_name
            keep_when_unused: The new value
            public: New value

        Returns: instance id

        """
        rows_str, cols_str, cells_str = self.objects.joiner(rows), self.objects.joiner(cols), self.objects.joiner \
            (cells)
        
        self.rows = rows_str
        self.cols = cols_str
        self.cells = cells_str
        if label_matrix_name:
            self.matrix_name = label_matrix_name
        self.keep_when_unused = keep_when_unused
        self.public = public
        
        return self.save()
    
    def delete(self, *args, **kwargs) -> bool:
        """
        Attempts to delete the LabelMatrix.
        It will not
        
        If the matrix should be kept if unused it will not
        be deleted.
        
        If there are still uses of the matrix it will not
        be deleted.
        
        Args:
            *args:
            **kwargs:

        Returns: None

        """
        if self.keep_when_unused is True:
            return False
        
        if self.job_label.all().count() > 1:
            return False
        
        super().delete(*args, **kwargs)
        return True
    
    @property
    def get_labels(self) -> tuple[list[str], list[str], list[str]]:
        return (self.rows.split(",,,"),
                self.cols.split(",,,"),
                self.cells.split(",,,"))
    
    @property
    def get_labels_with_2d_cells(self) -> tuple[list[str], list[str], list[list[str]]]:
        """
        Transforms the cell labels into a 2d structure in
        the format:
        
        [
        [A1, A2, A3],
        [B1, B2, B3]
        ]
        Returns:

        """
        rows, cols, cells = self.get_labels
        cells = [cells[i * len(cols):(i + 1) * len(cols)] for i in range(len(rows))]
        return rows, cols, cells

    