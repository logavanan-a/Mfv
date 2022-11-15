# Generated by Django 3.2.4 on 2022-06-20 12:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_reportmeta_sort_info'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reportmeta',
            options={'ordering': ['display_order'], 'verbose_name_plural': 'Report Meta'},
        ),
        migrations.AddField(
            model_name='reportmeta',
            name='page_slug',
            field=models.CharField(blank=True, max_length=500, null=True, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='reportmeta',
            name='report_slug',
            field=models.CharField(blank=True, max_length=500, null=True, unique=True, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z-]*$', 'Only alphanumeric characters are allowed.')]),
        ),
    ]