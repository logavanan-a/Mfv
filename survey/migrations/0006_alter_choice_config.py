# Generated by Django 4.2.13 on 2024-07-29 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_remove_choice_boundary_remove_language_states_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choice',
            name='config',
            field=models.JSONField(blank=True, default=list, null=True, verbose_name='Configurations'),
        ),
    ]
