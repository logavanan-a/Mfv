# Generated by Django 3.2.4 on 2022-07-01 11:24

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('application_master', '0006_auto_20220701_1124'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MissionData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('listing_order', models.PositiveIntegerField(default=0)),
                ('interface', models.CharField(choices=[('0', 'Web'), ('1', 'App'), ('2', 'Migrated Data')], default=1, max_length=2)),
                ('response', django.contrib.postgres.fields.jsonb.JSONField(default={})),
                ('created_on', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='application_master.mission')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
