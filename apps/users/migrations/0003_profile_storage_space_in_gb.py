# Generated by Django 5.1.2 on 2024-12-03 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_city_profile_country_profile_zip_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='storage_space_in_gb',
            field=models.FloatField(default=5),
        ),
    ]