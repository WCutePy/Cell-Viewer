

from django.db import models
from django.contrib.auth.models import User



class LabelMatrixManager(models.Manager):
    def create(self, request, rows: tuple[str], cols: tuple[str], cells: tuple[str]):
        joiner = lambda x: ",,,".join(x)
        rows_str, cols_str, cells_str = joiner(rows), joiner(cols), joiner(cells)
        
        equivalent = self.find_equivalent(len(rows), len(cols), rows_str, cols_str, cells_str)
        if equivalent is not None:
            return equivalent
        
        public = request.user.id in (1, 2, 3, 4)  # todo change this to a relevant check.
        
        saved = super().create(
            created_by_id=request.user.id,
            public=public,
            row_count=len(rows),
            col_count=len(cols),
            rows=joiner(rows),
            cols=joiner(cols),
            cells=joiner(cells),
        )
        return saved
    
    def get_all_visible(self, user: User | int):
        if isinstance(user, User):
            user = user.id
        return self.filter(user_id=user)
    
    def find_equivalent(self, row_count, col_count, rows_str, cols_str, cells_str) -> "LabelMatrix":
        return self.filter(
            row_count=row_count,
            col_count=col_count,
            rows=rows_str,
            cols=cols_str,
            cells=cells_str
        ).first()
    

class LabelMatrix(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    public = models.BooleanField()
    row_count = models.IntegerField()
    col_count = models.IntegerField()
    rows = models.TextField()
    cols = models.TextField()
    cells = models.TextField()
    
    objects = LabelMatrixManager()
