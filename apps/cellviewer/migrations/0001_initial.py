# Generated by Django 5.1.2 on 2024-12-16 15:52

import apps.cellviewer.models.SavedFile
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LabelMatrix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public', models.BooleanField()),
                ('matrix_name', models.CharField(default='unnamed', max_length=255)),
                ('keep_when_unused', models.BooleanField(default=False)),
                ('row_count', models.IntegerField()),
                ('col_count', models.IntegerField()),
                ('rows', models.TextField()),
                ('cols', models.TextField()),
                ('cells', models.TextField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=apps.cellviewer.models.SavedFile.saved_file_path_func)),
                ('storage_space_in_b', models.IntegerField()),
                ('row_count', models.IntegerField()),
                ('matrix_row_count', models.IntegerField()),
                ('matrix_col_count', models.IntegerField()),
                ('dimension', models.CharField(max_length=100)),
                ('hash', models.TextField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FilteredFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('substance_thresholds', models.TextField(default=None, null=True)),
                ('saved_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cellviewer.savedfile')),
            ],
        ),
        migrations.CreateModel(
            name='SavedJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('dimension', models.CharField(max_length=100)),
                ('files', models.ManyToManyField(related_name='job_files', through='cellviewer.FilteredFile', to='cellviewer.savedfile')),
                ('label_matrix', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_label', to='cellviewer.labelmatrix')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='filteredfile',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cellviewer.savedjob'),
        ),
    ]
