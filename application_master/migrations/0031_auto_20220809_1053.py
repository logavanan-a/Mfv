# Generated by Django 3.2.4 on 2022-08-09 10:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application_master', '0030_alter_missionindicatorcategory_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='district',
            options={'verbose_name_plural': '         District'},
        ),
        migrations.AlterModelOptions(
            name='donor',
            options={'verbose_name_plural': '  Donor'},
        ),
        migrations.AlterModelOptions(
            name='mission',
            options={'verbose_name_plural': '        Mission'},
        ),
        migrations.AlterModelOptions(
            name='missionindicator',
            options={'ordering': ['name'], 'verbose_name_plural': '      Mission Indicator'},
        ),
        migrations.AlterModelOptions(
            name='missionindicatorcategory',
            options={'ordering': ['name'], 'verbose_name_plural': '       Mission Indicator Category'},
        ),
        migrations.AlterModelOptions(
            name='missionindicatortarget',
            options={'verbose_name_plural': '   Mission Indicator Target'},
        ),
        migrations.AlterModelOptions(
            name='partner',
            options={'verbose_name_plural': '         Partner'},
        ),
        migrations.AlterModelOptions(
            name='partnermissionmapping',
            options={'verbose_name_plural': '     Partner Mission Mapping'},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'verbose_name_plural': '    Project'},
        ),
        migrations.AlterModelOptions(
            name='projectdonormapping',
            options={'verbose_name_plural': ' Project Donor Mapping'},
        ),
        migrations.AlterModelOptions(
            name='state',
            options={'verbose_name_plural': '          State'},
        ),
        migrations.AlterModelOptions(
            name='userpartnermapping',
            options={'verbose_name_plural': ' User Partner Mapping'},
        ),
    ]