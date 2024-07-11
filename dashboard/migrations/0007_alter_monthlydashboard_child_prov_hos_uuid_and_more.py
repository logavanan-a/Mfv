# Generated by Django 4.2.13 on 2024-07-11 12:57

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "dashboard",
            "0006_rename_children_referred_count_monthlydashboard_children_reffered_count",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="monthlydashboard",
            name="child_prov_hos_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="child_prov_spec_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="children_adv_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="children_covered_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="children_pres_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="children_prov_sgy_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="children_reffered_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="pgp_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="school_covered_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="swc_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
        migrations.AlterField(
            model_name="monthlydashboard",
            name="teachers_train_uuid",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=75), size=None
            ),
        ),
    ]
