# Generated by Django 3.2.4 on 2022-07-13 09:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0009_auto_20220713_0931'),
    ]

    operations = [
        migrations.RenameField(
            model_name='task',
            old_name='vision_centre',
            new_name='facility',
        ),
    ]