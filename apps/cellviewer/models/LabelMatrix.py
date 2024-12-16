
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, Value
from django.db.models.functions import Concat


def joiner(x):
    """a helper function that joins, using the specific character
    used to store the strings to the database.
    """
    return ",,,".join(x)


class LabelMatrixManager(models.Manager):
    def create(self, request, rows: tuple[str], cols: tuple[str], cells: tuple[str], label_matrix_name: str):
        rows_str, cols_str, cells_str = joiner(rows), joiner(cols), joiner \
            (cells)
        
        equivalent = self.find_equivalent(label_matrix_name, len(rows), len(cols), rows_str, cols_str, cells_str)
        if equivalent is not None:
            return equivalent
        
        public = request.user.id in \
        (1, 2, 3, 4)  # todo change this to a relevant check.
        
        saved = super().create(
            created_by_id=request.user.id,
            public=public,
            matrix_name=label_matrix_name,
            row_count=len(rows),
            col_count=len(cols),
            rows=joiner(rows),
            cols=joiner(cols),
            cells=joiner(cells),
        )
        
        if not label_matrix_name:
            saved.matrix_name = f"annotation-{saved.id}"
        saved.save()
        return saved
    
    def get_queryset(self):
        """Overrides the models.Manager method"""
        qs = super(LabelMatrixManager, self).get_queryset().annotate(
            dimension_string=Concat("row_count",Value("x"), 'col_count', output_field=models.TextField())
        )
        return qs
    
    def get_all_of_user(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        return self.filter(created_by=user)
    
    def find_equivalent(self, label_matrix_name, row_count, col_count, rows_str, cols_str,
                        cells_str) -> "LabelMatrix":
        return self.filter(
            matrix_name=label_matrix_name,
            row_count=row_count,
            col_count=col_count,
            rows=rows_str,
            cols=cols_str,
            cells=cells_str
        ).first()
    
    def get_all_same_size(self, user: User | int, row_count: int, col_count: int):
        """
        This will get all available matrixes of the same size.
        Currently any annotation matrix set to public with
        the same size will be shown along their own.
        On a larger userbase this would not be preferred.
        Args:
            user:
            row_count:
            col_count:

        Returns:

        """
        if isinstance(user, User):
            user = user.id
        query = (Q(created_by=user) | Q(public=True)) & \
                 Q(row_count=row_count) & Q(col_count=col_count)
        return self.filter(query)


class LabelMatrix(models.Model):
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
        rows_str, cols_str, cells_str = joiner(rows), joiner(cols), joiner \
            (cells)
        
        self.rows = rows_str
        self.cols = cols_str
        self.cells = cells_str
        self.label_matrix_name = label_matrix_name
        self.keep_when_unused = keep_when_unused
        self.public = public
        
        return self.save()
    
    def delete(self, *args, **kwargs):
        if self.keep_when_unused is True:
            return None
        
        if self.job_label.all().count() > 2:
            return None
        
        return super().delete(*args, **kwargs)
    
    @property
    def get_labels(self):
        return (self.rows.split(",,,"),
                self.cols.split(",,,"),
                self.cells.split(",,,"))
    
    @property
    def get_labels_with_2d_cells(self):
        rows, cols, cells = self.get_labels
        cells = [cells[i * len(cols):(i + 1) * len(cols)] for i in range(len(rows))]
        return rows, cols, cells

    