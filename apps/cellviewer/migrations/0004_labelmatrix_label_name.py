# Generated by Django 5.1.2 on 2024-12-06 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cellviewer', '0003_alter_savedjob_label_matrix'),
    ]

    operations = [
        migrations.AddField(
            model_name='labelmatrix',
            name='label_name',
            field=models.CharField(default='unnamed', max_length=255),
        ),
    ]
