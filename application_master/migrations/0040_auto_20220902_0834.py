# Generated by Django 3.2.4 on 2022-09-02 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_master', '0039_alter_userpartnermapping_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
