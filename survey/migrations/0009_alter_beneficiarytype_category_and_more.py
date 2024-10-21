# Generated by Django 4.2.13 on 2024-10-21 04:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("application_master", "0049_missionindicatortarget_periodicity_and_more"),
        ("survey", "0008_responseimportfiles_processed_file_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beneficiarytype",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="application_master.mission",
            ),
        ),
        migrations.AlterField(
            model_name="responseimportfiles",
            name="status",
            field=models.CharField(
                choices=[
                    ("Uploaded", "Uploaded"),
                    ("Inprogress", "Inprogress"),
                    ("Failed", "Failed"),
                    ("Imported", "Imported"),
                ],
                max_length=100,
                verbose_name="Status",
            ),
        ),
    ]