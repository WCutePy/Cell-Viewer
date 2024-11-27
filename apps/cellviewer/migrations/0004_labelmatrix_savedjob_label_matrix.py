# Generated by Django 5.1.2 on 2024-11-19 18:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cellviewer', '0003_remove_savedjob_file_path_savedjob_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LabelMatrix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public', models.BooleanField()),
                ('row_count', models.IntegerField()),
                ('col_count', models.IntegerField()),
                ('rows', models.TextField()),
                ('cols', models.TextField()),
                ('cells', models.TextField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='savedjob',
            name='label_matrix',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.PROTECT, to='cellviewer.labelmatrix'),
            preserve_default=False,
        ),
    ]