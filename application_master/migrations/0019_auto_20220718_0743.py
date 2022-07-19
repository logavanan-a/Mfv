# Generated by Django 3.2.4 on 2022-07-18 07:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application_master', '0018_auto_20220714_1358'),
    ]

    operations = [
        migrations.RenameField(
            model_name='facility',
            old_name='partner_mission_mapping',
            new_name='partner_mission_donor_mapping',
        ),
        migrations.AlterUniqueTogether(
            name='facility',
            unique_together={('name', 'partner_mission_donor_mapping')},
        ),
    ]