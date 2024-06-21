# Generated by Django 4.2.13 on 2024-06-21 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("application_master", "0044_auto_20240618_1131"),
        ("survey", "0004_beneficiarytype_beneficiaryresponse"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="choice",
            name="boundary",
        ),
        migrations.RemoveField(
            model_name="language",
            name="states",
        ),
        migrations.AddField(
            model_name="beneficiaryresponse",
            name="partner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="beneficiary_partner",
                to="application_master.partner",
            ),
        ),
        migrations.AlterField(
            model_name="errorlog",
            name="log_file",
            field=models.FileField(
                blank=True, null=True, upload_to="logfiles/%Y/%m/%d"
            ),
        ),
    ]