# Generated by Django 3.2.4 on 2022-07-06 04:52

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('application_master', '0008_auto_20220705_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='missionquestion',
            name='field_config',
            field=jsonfield.fields.JSONField(default=dict),
        ),
    ]