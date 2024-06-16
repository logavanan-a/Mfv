# Generated by Django 3.2.4 on 2024-06-16 15:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('masterdata', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppAnswerData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('interface', models.IntegerField(choices=[(0, 'Web'), (2, 'Android App')], default=0)),
                ('latitude', models.CharField(blank=True, max_length=255, null=True)),
                ('longitude', models.CharField(blank=True, max_length=255, null=True)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('version_number', models.CharField(blank=True, max_length=10, null=True)),
                ('app_version', models.CharField(blank=True, max_length=10, null=True)),
                ('language_id', models.CharField(blank=True, max_length=10, null=True)),
                ('imei', models.CharField(blank=True, max_length=100, null=True)),
                ('survey_id', models.CharField(blank=True, max_length=50, null=True)),
                ('mode', models.CharField(blank=True, max_length=50, null=True)),
                ('part2_charge', models.CharField(blank=True, max_length=50, null=True)),
                ('f_sy', models.CharField(blank=True, max_length=50, null=True)),
                ('gps_tracker', models.CharField(blank=True, max_length=10, null=True)),
                ('survey_status', models.CharField(blank=True, max_length=50, null=True)),
                ('created_on', models.DateTimeField(blank=True, null=True)),
                ('sp_s_o', models.DateTimeField(blank=True, null=True)),
                ('reason', models.CharField(blank=True, max_length=255, null=True)),
                ('cluster_id', models.CharField(blank=True, max_length=50, null=True)),
                ('cell_id', models.CharField(blank=True, max_length=100, null=True)),
                ('signal_strength', models.CharField(blank=True, max_length=50, null=True)),
                ('lac', models.CharField(blank=True, max_length=50, null=True)),
                ('mcc', models.CharField(blank=True, max_length=50, null=True)),
                ('mnc', models.CharField(blank=True, max_length=50, null=True)),
                ('la', models.CharField(blank=True, max_length=50, null=True)),
                ('carrier', models.CharField(blank=True, max_length=50, null=True)),
                ('network_type', models.CharField(blank=True, max_length=100, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('chargeleft', models.CharField(blank=True, max_length=20, null=True)),
                ('charge_connected', models.CharField(blank=True, max_length=50, null=True)),
                ('last_chargetime', models.CharField(blank=True, max_length=50, null=True)),
                ('sim_serialnumber', models.CharField(blank=True, max_length=100, null=True)),
                ('device_id', models.CharField(blank=True, max_length=100, null=True)),
                ('is_cus_rom', models.CharField(blank=True, max_length=50, null=True)),
                ('pe_r', models.CharField(blank=True, max_length=50, null=True)),
                ('ospr', models.CharField(blank=True, max_length=50, null=True)),
                ('lqc', models.CharField(blank=True, max_length=50, null=True)),
                ('sdc', models.CharField(blank=True, max_length=50, null=True)),
                ('dom_id', models.CharField(blank=True, max_length=50, null=True)),
                ('survey_part', models.CharField(blank=True, max_length=50, null=True)),
                ('c_status', models.CharField(blank=True, max_length=50, null=True)),
                ('stoken_sent', models.CharField(blank=True, max_length=255, null=True)),
                ('sample_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.PositiveIntegerField(choices=[(0, '------'), (1, 'Valid'), (2, 'Invalid')], default=0)),
                ('description', models.TextField(null=True)),
                ('model_name', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AppLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('help_text', models.CharField(blank=True, max_length=255, null=True)),
                ('other_text', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=500)),
                ('block_order', models.IntegerField(blank=True, null=True)),
                ('code', models.IntegerField(default=0)),
                ('language_code', models.JSONField(blank=True, default=dict, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataEntryLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=250)),
                ('slug', models.SlugField(blank=True, max_length=255, null=True, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(blank=True, max_length=255, null=True)),
                ('help_text', models.CharField(blank=True, max_length=255, null=True)),
                ('char_field1', models.CharField(blank=True, max_length=500, null=True)),
                ('char_field2', models.CharField(blank=True, max_length=500, null=True)),
                ('integer_field1', models.IntegerField(default=0)),
                ('integer_field2', models.IntegerField(default=0)),
                ('states', models.ManyToManyField(to='masterdata.Boundary')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('qtype', models.CharField(choices=[('T', 'Text Input'), ('S', 'Select One Choice'), ('R', 'Radio List'), ('C', 'Checkbox List'), ('D', 'Date'), ('I', 'Image'), ('GD', 'Grid with fixed rows'), ('In', 'Grid with vis_skip_questionariable rows'), ('AW', 'Address Widget'), ('AI', 'API'), ('F', 'File'), ('TA', 'Text Area'), ('AF', 'AutoFill and Calculate'), ('H', 'Hidden Question'), ('AP', 'Auto Populate'), ('TM', 'Time Widget'), ('SM', 'Select MasterLookup')], max_length=2, verbose_name='question type')),
                ('api_qtype', models.CharField(blank=True, choices=[('S', 'Select One Choice'), ('R', 'Radio List'), ('C', 'Checkbox List'), ('T', 'Text'), ('RO', 'Read Only')], max_length=2, null=True, verbose_name='api question type')),
                ('text', models.CharField(max_length=500, verbose_name='question text')),
                ('validation', models.IntegerField(blank=True, choices=[(0, 'Digit'), (1, 'Number'), (2, 'Alphabet'), (3, 'Alpha Numeric'), (4, 'No Validation'), (6, 'Mobile Number'), (7, 'Landline'), (8, 'Date'), (9, 'Time'), (10, 'Only Alpha Numeric')], null=True)),
                ('question_order', models.IntegerField(blank=True, null=True)),
                ('code', models.IntegerField(default=0)),
                ('help_text', models.CharField(blank=True, max_length=500)),
                ('mandatory', models.BooleanField(default=True)),
                ('display', models.PositiveIntegerField(default=0)),
                ('hidden', models.PositiveIntegerField(default=0)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_profile', models.BooleanField(default=False)),
                ('is_grid', models.BooleanField(default=False)),
                ('language_code', models.JSONField(blank=True, default=dict, null=True)),
                ('display_inline', models.BooleanField(default=False)),
                ('address_question', models.BooleanField(default=False)),
                ('allow_multiple', models.BooleanField(default=False)),
                ('api_json', models.JSONField(blank=True, default=dict, null=True, verbose_name='API Json')),
                ('display_has_name', models.BooleanField(default=False)),
                ('parent_question', models.BooleanField(default=False)),
                ('is_editable', models.BooleanField(default=True)),
                ('training_config', models.JSONField(blank=True, default=dict, null=True, verbose_name='Training configuration')),
                ('code_display', models.CharField(blank=True, max_length=200, null=True)),
                ('question_filter', models.PositiveIntegerField(choices=[(0, 'No'), (1, 'Yes')], default=0, verbose_name='Show as filter')),
                ('short_text', models.CharField(blank=True, max_length=500, null=True)),
                ('deactivated_reason', models.CharField(blank=True, choices=[('Program Discontinued', 'Program Discontinued'), ('Program Major Revamp', 'Program Major Revamp'), ('Others', 'Others')], max_length=500, null=True)),
                ('deactivated_date', models.DateTimeField(blank=True, null=True)),
                ('form_question_number', models.CharField(blank=True, max_length=20, null=True)),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.block', verbose_name='Blocks')),
                ('deactivated_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('master_question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='masterdata.masterlookup')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.question')),
            ],
            options={
                'ordering': ('block', 'question_order'),
            },
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('survey_type', models.IntegerField(choices=[(0, 'OneTime Activity'), (1, 'Extended activity')], default=0)),
                ('slug', models.SlugField(max_length=255, unique=True, verbose_name='slug')),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('survey_order', models.PositiveIntegerField(default=0, verbose_name='order')),
                ('display_type', models.CharField(choices=[('single', 'single'), ('multiple', 'multiple')], default='multiple', max_length=25)),
                ('periodicity', models.IntegerField(choices=[(0, '---NA---'), (1, 'Daily'), (2, 'Weekly'), (3, 'Monthly'), (4, 'Quarterly'), (5, 'Half Yearly'), (6, 'Yearly'), (7, 'Onetime activity')], default=0, verbose_name='Periodicity')),
                ('expiry_age', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('config', models.JSONField(default=dict)),
                ('extra_config', models.JSONField(default=dict)),
                ('procedure_func', models.CharField(blank=True, max_length=100, null=True)),
                ('capture_level_type', models.IntegerField(choices=[(1, 'Web'), (2, 'App'), (3, 'Both')], default=3)),
                ('form_entry_level', models.PositiveIntegerField(blank=True, default=1, null=True)),
                ('survey_module', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('report_generated', models.DateTimeField(blank=True, null=True)),
                ('report_filename', models.CharField(blank=True, max_length=2500, null=True)),
                ('deactivated_reason', models.CharField(blank=True, choices=[('Program Discontinued', 'Program Discontinued'), ('Program Major Revamp', 'Program Major Revamp'), ('Others', 'Others')], max_length=500, null=True)),
                ('deactivated_date', models.DateTimeField(blank=True, null=True)),
                ('short_name', models.CharField(blank=True, max_length=100, null=True)),
                ('categories', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='Survey_Category', to='masterdata.masterlookup')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('data_entry_level', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.dataentrylevel')),
                ('deactivated_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('surveyparent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='Parent_Survey', to='survey.survey')),
                ('theme', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='masterdata.masterlookup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Validations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('validation_type', models.CharField(blank=True, max_length=255, null=True)),
                ('code', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VersionUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('version_code', models.IntegerField(default=0)),
                ('version_name', models.CharField(blank=True, max_length=100, null=True)),
                ('force_update', models.BooleanField(default=True)),
                ('date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('version_number', models.CharField(blank=True, max_length=255, null=True)),
                ('changes', models.CharField(blank=True, max_length=255, null=True)),
                ('action', models.CharField(blank=True, max_length=255, null=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('create_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.survey')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveySkip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('skip_level', models.CharField(blank=True, max_length=255, null=True)),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.question')),
                ('skipto_survey', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='skipto_survey', to='survey.survey')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='survey', to='survey.survey')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('log_value', models.CharField(blank=True, max_length=255, null=True)),
                ('other_text', models.CharField(blank=True, max_length=255, null=True)),
                ('create_by', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.version')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyDisplayQuestions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('display_type', models.CharField(choices=[('0', 'Web'), ('1', 'Android'), ('2', 'Report'), ('3', 'SearchFilter')], max_length=100)),
                ('questions', models.JSONField(default=dict)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.survey')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResponseFiles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('response_image', models.FileField(blank=True, null=True, upload_to='static/%Y/%m/%d')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('creation_key', models.CharField(blank=True, max_length=100, null=True, verbose_name='UUID')),
                ('approve', models.BooleanField(default=False)),
                ('reject', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.question')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionValidation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('max_value', models.CharField(blank=True, max_length=100, null=True)),
                ('min_value', models.CharField(blank=True, max_length=100, null=True)),
                ('message', models.CharField(blank=True, max_length=255, null=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.question')),
                ('validationtype', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.validations')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QuestionLanguageValidation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('text', models.CharField(max_length=255)),
                ('other_text', models.CharField(blank=True, max_length=255, null=True)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.language')),
                ('questionvalidation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.questionvalidation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProjectLevels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('projectlevel_order', models.IntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('submission_date', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='static/%Y/%m/%d')),
                ('sfile', models.FileField(blank=True, null=True, upload_to='static/surveyfiles/%Y/%m/%d')),
                ('app_answer_on', models.DateTimeField(blank=True, null=True)),
                ('app_answer_data', models.CharField(blank=True, max_length=255, null=True)),
                ('unqid', models.CharField(blank=True, max_length=255, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='media', to='survey.question', verbose_name='question')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='media', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Levels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('level_order', models.IntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.survey')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='JsonAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('creation_key', models.CharField(max_length=75, unique=True)),
                ('submission_date', models.DateTimeField(auto_now=True)),
                ('app_answer_on', models.DateTimeField(blank=True, null=True)),
                ('app_answer_data', models.PositiveIntegerField(blank=True, null=True)),
                ('response', models.JSONField(default=dict)),
                ('cluster', models.JSONField(default=dict)),
                ('interface', models.CharField(choices=[('0', 'Web'), ('1', 'App'), ('2', 'Migrated Data')], default=1, max_length=2)),
                ('json_order', models.PositiveIntegerField(blank=True, null=True)),
                ('inner_response_creation_key', models.CharField(blank=True, max_length=50, null=True)),
                ('facility_id', models.IntegerField(blank=True, db_index=True, default=0, null=True)),
                ('language', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.language')),
                ('lead_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='leadusers', to=settings.AUTH_USER_MODEL, verbose_name='leadusers')),
                ('survey', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='survey.survey')),
                ('training_survey', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='training_survey', to='survey.survey')),
                ('training_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='masterdata.masterlookup')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='jsonanswers', to=settings.AUTH_USER_MODEL, verbose_name='jsonuser')),
            ],
        ),
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('stoken', models.CharField(blank=True, max_length=255, null=True)),
                ('log_file', models.FileField(blank=True, null=True, upload_to='media/logfiles/%Y/%m/%d')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DeviceDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('submission_date', models.DateTimeField(auto_now=True)),
                ('app_size', models.CharField(blank=True, max_length=20, null=True)),
                ('disk_free_space', models.CharField(blank=True, max_length=20, null=True)),
                ('primary_storage', models.CharField(blank=True, max_length=20, null=True)),
                ('secondary_storage', models.CharField(blank=True, max_length=20, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('text', models.CharField(max_length=500, verbose_name='choice text')),
                ('code', models.IntegerField()),
                ('choice_order', models.FloatField(blank=True)),
                ('language_code', models.JSONField(blank=True, default=dict, null=True)),
                ('is_other_choice', models.BooleanField(default=False)),
                ('config', models.JSONField(blank=True, default=dict, null=True, verbose_name='Configurations')),
                ('code_display', models.IntegerField(blank=True, default=0, null=True)),
                ('score', models.FloatField(blank=True, default=0, null=True)),
                ('uuid', models.CharField(blank=True, max_length=100, null=True, verbose_name='UUID')),
                ('deactivated_reason', models.CharField(blank=True, choices=[('Program Discontinued', 'Program Discontinued'), ('Program Major Revamp', 'Program Major Revamp'), ('Others', 'Others')], max_length=500, null=True)),
                ('deactivated_date', models.DateTimeField(blank=True, null=True)),
                ('boundary', models.ManyToManyField(to='masterdata.Boundary')),
                ('deactivated_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='choices', to='survey.question', verbose_name='question')),
                ('skip_question', models.ManyToManyField(related_name='skip_question', to='survey.Question')),
            ],
            options={
                'ordering': ('question', 'choice_order'),
            },
        ),
        migrations.AddField(
            model_name='block',
            name='survey',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.survey'),
        ),
        migrations.CreateModel(
            name='AppLoginDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('surveyversion', models.CharField(blank=True, max_length=10, null=True)),
                ('lang_code', models.CharField(blank=True, max_length=10, null=True)),
                ('tabtime', models.DateTimeField(blank=True, null=True)),
                ('sdc', models.PositiveIntegerField(default=0)),
                ('itype', models.CharField(blank=True, max_length=10, null=True)),
                ('version_number', models.CharField(blank=True, max_length=10, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LanguageTranslationText',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'Deleted'), (2, 'Active'), (3, 'Inactive')], default=2)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('text', models.CharField(blank=True, max_length=500, null=True)),
                ('message', models.CharField(blank=True, max_length=500, null=True)),
                ('help_text', models.CharField(blank=True, max_length=500, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='survey.language')),
            ],
            options={
                'unique_together': {('content_type', 'object_id', 'language')},
            },
        ),
        migrations.AddIndex(
            model_name='jsonanswer',
            index=models.Index(fields=['survey_id', 'user_id'], name='survey_json_survey__f3cd8f_idx'),
        ),
    ]
