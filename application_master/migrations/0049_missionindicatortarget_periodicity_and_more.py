# Generated by Django 4.2.13 on 2024-09-18 08:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("application_master", "0048_remove_project_application_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="missionindicatortarget",
            name="periodicity",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="missionindicatortarget",
            name="target",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]