# Generated by Django 4.2.13 on 2024-07-09 16:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0005_monthlydashboard_creation_key"),
    ]

    operations = [
        migrations.RenameField(
            model_name="monthlydashboard",
            old_name="children_referred_count",
            new_name="children_reffered_count",
        ),
    ]
