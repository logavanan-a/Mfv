# Generated by Django 3.2.4 on 2022-07-04 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_master', '0006_auto_20220701_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='missionindicator',
            name='indicator_type',
            field=models.IntegerField(choices=[(1, 'Gender Base'), (2, 'Total')], default=1, max_length=2),
        ),
    ]
