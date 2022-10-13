# Generated by Django 3.2.4 on 2022-10-13 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardSummaryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(2, 'Active'), (0, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('listing_order', models.PositiveIntegerField(default=0)),
                ('log_key', models.CharField(max_length=500, unique=True)),
                ('last_successful_update', models.DateTimeField(blank=True, null=True)),
                ('most_recent_update', models.DateTimeField(blank=True, null=True)),
                ('most_recent_update_status', models.CharField(blank=True, max_length=2500, null=True)),
                ('most_recent_update_time_taken_millis', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
