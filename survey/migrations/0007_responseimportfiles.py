# Generated by Django 4.2.13 on 2024-08-08 15:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("application_master", "0047_userprofile"),
        ("survey", "0006_alter_choice_config"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponseImportFiles",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "active",
                    models.PositiveIntegerField(
                        choices=[(2, "Active"), (0, "Inactive")], default=2
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                ("listing_order", models.PositiveIntegerField(default=0)),
                (
                    "response_image",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="media/import-response/%Y/%m/%d",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Uploaded", "Uploaded"),
                            ("Inprogress", "Inprogress"),
                            ("Failed", "Failed"),
                            ("Imported", "Imported"),
                        ],
                        verbose_name="Status",
                    ),
                ),
                ("error_details", models.TextField(blank=True, null=True)),
                ("imported_on", models.DateTimeField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="application_master.project",
                    ),
                ),
                (
                    "survey",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="survey.survey",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]