# Generated by Django 3.2.4 on 2024-05-09 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0021_auto_20240509_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataentryremark',
            name='reject_reason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
