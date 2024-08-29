# Generated by Django 4.2.13 on 2024-08-29 11:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0009_chartmeta"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="monthlydashboard",
            name="month",
        ),
        migrations.AddField(
            model_name="monthlydashboard",
            name="end_date",
            field=models.DateField(
                default=datetime.datetime(2024, 8, 29, 17, 12, 46, 288824)
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="monthlydashboard",
            name="start_date",
            field=models.DateField(
                default=datetime.datetime(2024, 8, 29, 17, 13, 2, 981344)
            ),
            preserve_default=False,
        ),
    ]
