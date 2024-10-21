# Generated by Django 4.2.13 on 2024-09-16 10:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("application_master", "0047_userprofile"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="application_type",
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="login_type",
            field=models.PositiveIntegerField(
                choices=[(1, "WEB"), (2, "APP"), (3, "BOTH")]
            ),
        ),
        migrations.CreateModel(
            name="UserActivityDate",
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
                ("activity_date", models.DateField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]