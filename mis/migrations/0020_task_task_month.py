# Generated by Django 3.2.4 on 2022-10-10 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0019_dataentryremark'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='task_month',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
