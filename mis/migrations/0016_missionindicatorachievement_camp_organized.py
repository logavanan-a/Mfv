# Generated by Django 3.2.4 on 2022-08-23 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0015_alter_task_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='missionindicatorachievement',
            name='camp_organized',
            field=models.IntegerField(blank=True, choices=[(1, 'Drivers'), (2, 'Truckers'), (3, 'Carpenters')], null=True),
        ),
    ]
