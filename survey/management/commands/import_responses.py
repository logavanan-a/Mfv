from django.core.management.base import BaseCommand, CommandError
from survey.models import ResponseImportFiles,Question,QuestionValidation,Choice,JsonAnswer,Survey,BeneficiaryResponse
from application_master.models import Boundary,BoundaryLevel,Project,UserProjectMapping
from django.db.models import F,Q
import pandas as pd
from mfv_mis.settings import *
from collections import defaultdict
from datetime import datetime, date
from uuid import uuid4
import json,requests,ast,re
from survey.form_views import load_data_to_cache_boundary_meta
from cache_configuration.views import load_data_to_cache_project,load_data_to_cache_survey,load_data_to_cache_questions
from django.utils import timezone
import logging
import sys, traceback
import ipdb
import numpy as np
import subprocess
from io import BytesIO
from django.core.files.base import ContentFile
from send_mail.views import send_mail
from send_mail.models import MailTemplate,MailData
# Mandatories 
# TODO: Project, State, District, Block,Gram Panchayath, Village, Generation Key, -- All questions related to that form
# TODO: Unique validation required for unique fields like aadhar , ration card and other
logger = logging.getLogger(__name__)

API_URL = f"{HOST_URL}/api/v1/push/"
USER_ID = 369#admin
chunk_size = RESPONSE_IMPORT['WEB_IMPORT_CHUNK_SIZE']

class Command(BaseCommand):

    """ Command To update import the responses uploaded in excel."""
    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-s', '--survey_list', type=int, nargs='+'  )
        parser.add_argument('-p', '--project_list', type=int, nargs='+'  )
          
    def handle(self,*args, **options):
        try:
            imp_start = datetime.now()
            logger.info('Importing Responses - time taken:' + str(imp_start))
            survey_id = options.get('survey_list')
            project_id = options.get('project_list')
            response_files = ResponseImportFiles.objects.filter(active=2, status__in=['Uploaded']) 
            if survey_id and project_id:
                response_files = response_files.filter(survey_id__in = survey_id,project_id__in=project_id)
            response_files = response_files.values('survey_id').annotate(response_image=F('response_image'),response_id=F('id'))
            
            errors = defaultdict(list)
            for response in response_files:
                logger.info('Importing Responses Id :'+str(response['response_id'])+' - '+str(survey_id)+' - '+str(project_id))
                t1 = datetime.now()
                response_obj = ResponseImportFiles.objects.get(id=response['response_id'])
                response_obj.status = 'Inprogress'
                response_obj.save()
                try:
                    error = []
                    survey_id = response.get('survey_id')
                    response_file = response.get('response_image')
                    processed_file_name = datetime.now().strftime('%Y%m%d%H%M%S')+'_' + response_file.split('/')[-1]
                    processed_file = RESPONSE_IMPORT['PROCESSED_FILE_PATH'] + processed_file_name
                    df = pd.read_excel(MEDIA_ROOT+'/'+response_file,dtype=str)
                    # ipdb.set_trace()
                    df = questions_validation(df,survey_id,response_obj.project_id)

                    # df['Activity Date'] = pd.to_datetime(df['Activity Date'], format='%Y/%m/%d', errors='coerce').dt.strftime('%d-%m-%Y')
                    if 'Error Message' in df.columns and df['Error Message'].notnull().any():
                        response_obj.status = 'Failed'
                        response_obj.error_details = 'Please validate the file for errors in the "Error Message" column'
                        df.to_excel(BASE_DIR+processed_file,index=False)
                        response_obj.processed_file = processed_file
                        response_obj.save()
                        continue

                    parsed_data = parse_data_row(df,survey_id)
                    sliced_data = [parsed_data[i:i+chunk_size] for i in range(0, len(parsed_data), chunk_size)]
                    response_data = []
                    
                    # get the data entry op based on the project id
                    data_entry_op = list(UserProjectMapping.objects.filter(active=2,project_id=response_obj.project_id,user__groups__id=1).values_list('user_id'))
                    
                    for data in sliced_data:
                        response_data.append(push_data_to_api(data,data_entry_op[0] if data_entry_op else USER_ID))
                    application_issue = [item for item in response_data if not item.get('status') ]
                    

                    has_sync_status_0 = {sync_item['r_uuid']:sync_item['error_msg'] for item in response_data for sync_item in item['sync_res'] if sync_item['sync_status'] != 2}
                    df['Status - Error'] = df['Generation Key'].apply(lambda value: f'Failed - {has_sync_status_0.get(value)}' if has_sync_status_0.get(value) else 'Success')
                    
                    df.to_excel(BASE_DIR+processed_file,index=False)
                    
                    # Permission command for file
                    permission_command = RESPONSE_IMPORT['FILE_PERMISSION_COMMAND'].format(processed_file)
                    result = subprocess.run(permission_command.split(' '), capture_output=True, text=True)

                    error_details = ""
                    if has_sync_status_0:
                        response_obj.status = 'Failed'
                        error_details = "Download the file and refer to the error section at the end for details. Remove any successful records before re-uploading."
                    elif not application_issue:
                        response_obj.status = 'Imported'
                        response_obj.imported_on = timezone.now()
                        response_obj.processed_file = processed_file
                        error_details = "Download the file for each record's status."
                    if application_issue:
                        error_details = response_obj.error_details + f"\n Failed Batches - {application_issue}"
                    
                    count_of_records = f"""   <br><b>Total Records Imported: </b>{len(df)}<br>
                                            <b>Records Imported Successfully: </b>{len(df) - len(has_sync_status_0)}<br>
                                            <b>Records with Import Errors: </b>{len(has_sync_status_0)} <br>"""
                    response_obj.error_details = error_details+count_of_records
                    response_obj.save()
                    t2 = datetime.now()
                    logger.info('Response Imported - ' + ':(' +str(response['response_id']) + ') - time taken:' + str(t2-t1) )

                    logger.info('Sending Mail...!')
                    to_mail_ids = get_all_role_user(response_obj.project) + ACTIVITY_MAIL_RECIEVER
                    mail_template = MailTemplate.objects.get(active=2,template_name='Data Upload')
                    mail_subject = mail_template.subject.format(survey_name=response_obj.survey.name,project_name=response_obj.project.name)
                    record_url = f'<a href="{HOST_URL}/manage/activity/import-responses/{response_obj.project_id}" target="_blank">Click here</a>'
                    mail_content = mail_template.content.format(survey_name=response_obj.survey.name,project_name=response_obj.project.name,record_url=record_url,total_count=len(df),success_count=len(df) - len(has_sync_status_0),error_count=len(has_sync_status_0),error_details=error_details)
                    
                    # Sending mail..
                    response = send_mail(to_mail_ids,mail_subject,mail_content)
                    mail_status = 3 if response['status'] == 200 else 1
                    send_data_obj = MailData.objects.create(subject = mail_subject,content = mail_content,mail_to = ';'.join([item for item in to_mail_ids if item]),
                                                        priority = 1,mail_status = mail_status, send_attempt = 1,mail_cc="",mail_bcc="",
                                                        template_name = mail_template,error_details = str(response) )

                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    logger.error(error_stack) 
                    response_obj.error_details = error_stack
                    response_obj.save()
                    print(error_stack)

                    # continue

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logger.error(error_stack) 
            print(error_stack)



def questions_validation(df,survey_id,project_id):

    survey = Survey.objects.get(id=survey_id)
    project = Project.objects.get(id=project_id)

    aw_question = Question.objects.filter(active=2,block__survey_id=survey_id,qtype="AW")
    #removing the error message columns if uploaded error sheet after correction
    if 'Error Message' in df.columns:
        df.drop(columns='Error Message', inplace=True)

    # ipdb.set_trace()
    unique_ids = RESPONSE_IMPORT['unique_id']
    if unique_ids.get(str(survey_id)):
        unique_ids = RESPONSE_IMPORT['unique_id']
        reference_question = Question.objects.get(id = unique_ids.get(str(survey_id)))
        column = reference_question.text.strip()
        # ben_survey_id = reference_question.block.survey_id
        question_id = unique_ids.get(str(survey_id))
        column_df = df[column][df[column].notna()]
        unique_values = column_df.astype(str).explode().dropna().loc[lambda x: x != ''].tolist()
        beneficiary_dict = get_beneficiary_unique_values(survey_id,question_id,unique_values)
        mask = df[column].astype(str).isin(list(beneficiary_dict.keys()))
        final_mask = mask & (df['Generation Key'] != df[column].astype(str).map(beneficiary_dict))
        if final_mask.any():
            error_message =  f"* Please check {column} data should be unique."
            df.loc[mask, 'Error Message'] = error_message
    

    # Filter rows where 'Project' is null or not project name
    df['Project'] = df['Project'].str.strip() if df['Project'].dtype == 'object' else df['Project']
    project_name_not_matching = df[df['Project'].isna() | (df['Project'] != project.name)]
    
    if not project_name_not_matching.empty:
        error_message =  f"* Please ensure the Project Name is up to date."
        df['Error Message'] = ''
        df.loc[project_name_not_matching.index.tolist(), 'Error Message'] = error_message

    # first validating the AW question because it have the all level data like , state ,district, and other
    if aw_question or (survey.survey_type == 1 and survey.data_entry_level_id == 1): #location based survey
        boundary_names_lower = set(map(str.lower, Boundary.objects.values_list('name', flat=True)))
        boundary_levels = BoundaryLevel.objects.filter(active=2).values_list('name',flat=True)
        
        df_lower = df[boundary_levels].applymap(lambda x: str(x).lower())
        missing_values = df_lower[~df_lower.isin(boundary_names_lower)]
        if not missing_values.empty:
            missing_values.isnull().isin([False]).any(axis=1)
            error_message =  f"* Please check the all location data is correct or not."
            df.loc[missing_values.isnull().isin([False]).any(axis=1), 'Error Message'] = error_message

    #TODO : Need to get the all questions related to all survey at once, now we are quering inside the loop
    # Here cache is not used because to get the updated questions
    questions = Question.objects.filter(active=2,block__survey_id=survey_id,is_grid=False).exclude(qtype__in=['GD','AW'])
    row_grid_question = Question.objects.filter(active=2,block__survey_id=survey_id,is_grid=True)

    questions_validations = {i.question_id:i for i in QuestionValidation.objects.filter(active=2,question__block__survey_id=survey_id)}

    if 'Generation Key' in df.columns and df['Generation Key'].any():
        creation_df = df['Generation Key'][df['Generation Key'].notna()]
        all_creation_key = list(JsonAnswer.objects.filter(active=2,survey_id=survey_id).values_list('creation_key',flat=True))
        creation_key_exists = creation_df[~creation_df.isin(all_creation_key)].index.tolist()
        if creation_key_exists:
            error_message = f"* Generation Key is not exists .Please check."
            df.loc[creation_key_exists, 'Error Message'] = error_message        


    # # Validate each date column
    for question in questions:
        column = question.text 
        validation = questions_validations.get(question.id)
             
        # first validating the AW question because it have the all level data like , state ,district, and other
        # if question.qtype == 'AW':
        #     boundary_names_lower = set(map(str.lower, Boundary.objects.values_list('name', flat=True)))
        #     boundary_levels = BoundaryLevel.objects.filter(active=2).values_list('name',flat=True)
           
        #     df_lower = df[boundary_levels].applymap(lambda x: str(x).lower())
        #     missing_values = df_lower[~df_lower.isin(boundary_names_lower)]
        #     if not missing_values.empty:
        #         missing_values.isnull().isin([False]).any(axis=1)
        #         error_message =  f"Please check the all location data is correct or not."
        #         df.loc[missing_values.isnull().isin([False]).any(axis=1), 'Error Message'] = error_message
            
        #     continue
        if question.parent and question.parent.qtype == 'GD' :
            for row_grid in row_grid_question.filter(parent=question.parent):
                column = f"{question.parent.text}--{row_grid.text}.{question.text}"
                columns = df[column.strip()]
                question_based_validation(df,question,columns,validation,column)
            continue
        
        if question.qtype == 'AI':
            column = get_api_column_name(question)
             # static validating for given project and school landline number in same location or not
            project_linked_schools = get_school_based_project(project.district_id)
            # import ipdb;ipdb.set_trace()
            mask = ~df[column].apply(lambda value: any(val.strip() in project_linked_schools for val in str(value).split(',')))
            if mask.any():
                error_message =  f"* Please check the given Project and {column} are in same location."
                df.loc[mask, 'Error Message'] = error_message

        # text type fields with validation
        columns = df[column]
        question_based_validation(df,question,columns,validation,column)
    
    return df

def question_based_validation(df,question,columns,validation,column):
    # Define a dictionary to map validation types to validation functions
    validation_functions = {
        1: lambda x: x.astype(str).str.isdigit(),
        2: lambda x: x.astype(str).apply(lambda s: bool(re.match(r'^-?\d*\.?\d+$', s))),
        3: lambda x: x.astype(str).str.match(r'^[A-Za-z\s]+$'),
        4: lambda x: x.astype(str).str.match(r'^[A-Za-z0-9\s]+$'),
    }
    # validating the mandatory questions are filled or not
    if question.mandatory and columns.isna().any():
        df.loc[columns.isna(),'Error Message'] = f"Ensure that the {column} field is filled in for all mandatory fields."
    elif not question.mandatory:
        columns = df[column][df[column].notna()]
    
    if question.qtype == 'T' and validation and validation.validationtype_id:
        is_valid = validation_functions.get(validation.validationtype_id)(columns)
        not_valid_index = columns[~is_valid].index.tolist()
        if validation.max_value and validation.min_value and validation.validationtype_id in [1,2]:
            numeric_values = pd.to_numeric(columns, errors='coerce')
            is_within_range = (numeric_values >= int(validation.min_value)) & (numeric_values <= int(validation.max_value))
        elif validation.max_value and validation.min_value and not df[column].isna().all():
            value_lengths = columns.str.len()
            is_within_range = (value_lengths >= int(validation.min_value)) & (value_lengths <= int(validation.max_value))
        
        # is_not_within_range_index = columns[~is_within_range].index.tolist()

        if not_valid_index:
            error_message =  f"* Validate that the {column} value is in the correct format. It should be in {validation.validationtype.validation_type}."
            df.loc[not_valid_index, 'Error Message'] = error_message

        if not df[column].isna().all() and columns[~is_within_range].index.tolist():
            df.loc[columns[~is_within_range].index.tolist(), 'Error Message'] = f"Ensure that the '{column}' value is within the specified range. Minimum: {validation.min_value} and Maximum: {validation.max_value}."
    
    elif question.qtype == 'D':
        validation_date_format = "%d%m%Y"
        is_valid_date_format = pd.to_datetime(columns, format='%Y/%m/%d', errors='coerce').dt.strftime('%Y/%m/%d') == columns
        copy_df = df[column][df[column].notna()]
        # invalid_dates = copy_df[~is_valid_date_format]
        invalid_indices = copy_df[~is_valid_date_format].index.tolist()
        if invalid_indices:
            error_message = f"* Invalid date format found in the '{column}' column. Please ensure all dates are in the yyyy/mm/dd format."
            # copy_df.loc[~is_valid_date_format, 'Error Message'] = error_message
            df.loc[invalid_indices, 'Error Message'] = error_message
        if validation and not invalid_indices:
            max_value = validation.max_value.replace('00000000',datetime.today().strftime('%d%m%Y'))
            min_value = validation.min_value.replace('00000000',datetime.today().strftime('%d%m%Y'))
            start_date = pd.to_datetime(min_value, format=validation_date_format)
            end_date = pd.to_datetime(max_value, format=validation_date_format)
            
            # Filter the DataFrame to get dates within the specified range
            is_within_validation_range = (pd.to_datetime(columns) >= start_date) & (pd.to_datetime(columns) <= end_date)
            # filtered_dates = copy_df[~is_within_validation_range]
            filtered_dates_indices = copy_df[~is_within_validation_range].index.tolist()
            if filtered_dates_indices:
                error_message = f"* Dates are not within the specified range ({start_date} to {end_date})."
                df.loc[filtered_dates_indices, 'Error Message'] = error_message
                # copy_df.loc[~is_within_validation_range, 'Error Message'] = error_message
    elif question.qtype in ['C','S','R']:
        choices = Choice.objects.filter(question=question).values_list('text',flat=True)
        choices_str = list(map(lambda x: x.lower(), choices))
        copy_df = df[column][df[column].notna()].astype(str)
        columns = copy_df.str.lower().str.strip().str.split(',')
        validated_columns = columns.apply(lambda x: all(val.lower() in choices_str for val in x))
        invalid_choices_index = columns[~validated_columns].index.tolist()
        if invalid_choices_index:
            error_message = f"* Ensure that the value in the '{column}' column is one of the following: {list(choices)}."
            df.loc[invalid_choices_index, 'Error Message'] = error_message
    elif question.qtype == 'AI':
        unique_ids = RESPONSE_IMPORT['unique_id']
        reference_question = Question.objects.filter(id__in = question.api_json.get('lname_que_id').split(',')).first()
        ben_survey_id = reference_question.block.survey_id
        question_id = unique_ids.get(str(ben_survey_id))
        copy_df = df[column][df[column].notna()]
        unique_values = copy_df.astype(str).str.lower().str.strip().str.split(',').explode().dropna().loc[lambda x: x != ''].tolist()
        beneficiary_dict = get_beneficiary_unique_values(ben_survey_id,question_id,unique_values)
        df[column] = df[column].astype(str)
        df[column+'-API'] =  df[column].apply(lambda value: [str(beneficiary_dict.get(v.strip(), "")) for v in value.split(',') if v.strip()])
        if len(set(unique_values)) != len(set(beneficiary_dict)):
            copy_df['all_values_exist'] = copy_df.astype(str).apply(lambda x: unique_id_validation(x,beneficiary_dict))
            unique_id_error = columns[~copy_df['all_values_exist']].index.tolist()
            if unique_id_error:
                error_message =  f"* Validate the value of the {column} question is correct. It does not exist in our database."
                df.loc[unique_id_error, 'Error Message'] = error_message
        
def get_beneficiary_unique_values(ben_survey_id,question_id,unique_values):
    #TODO : better query need to update , for time being added below
    beneficiary_data = JsonAnswer.objects.filter(active=2,survey_id=ben_survey_id)
    data = {i.response.get(question_id):i.creation_key for i in beneficiary_data if i.response.get(question_id) in unique_values }
    return data

def unique_id_validation(values,ben_dict):
    for value in values.split(','):
        if value and value.strip().lower() not in ben_dict:
            return False
    return True

def push_data_to_api(data,user_id):
    response_data = {
        'u_uuid': user_id,
        'd_uuid': '',
        'pushInput': json.dumps(data),
    }
    # import ipdb;ipdb.set_trace()
    response = requests.post(API_URL, data=response_data)
    if response.status_code != 200:
        return {"error":response.text}
    return json.loads(response.content.decode('utf-8'))

def parse_data_row(df,survey_id):
    #TODO: temprorty - need to cache
    questions = Question.objects.filter(active=2,block__survey_id=survey_id,parent=None)
    all_projects = load_data_to_cache_project()
    projects = dict(zip(all_projects.values(), all_projects.keys()))
    # all_boundaries = load_data_to_cache_boundary_meta()
    # boundaries = dict(zip(all_boundaries.values(), all_boundaries.keys()))
    survey = Survey.objects.get(id=survey_id)
    if survey.survey_type == 1 and survey.data_entry_level_id == 1: #location based survey
        # survey.get_survey_location_v3()
        boundary_level = survey.config[0]['object_id_2']
        boundary_level = BoundaryLevel.objects.get(id=boundary_level)
        boundary_data = dict(Boundary.objects.filter(active=2,boundary_level_type_id=boundary_level).values_list('name','id'))
    elif survey.survey_type == 0:
        boundary_levels = BoundaryLevel.objects.filter(active=2).order_by('code')
        boundary_data = {i.name.lower():str(i.id) for i in Boundary.objects.filter(active=2)}

    final_result = []
    ai_questions = questions.filter(qtype='AI')
    if ai_questions:
        api_column = get_api_column_name(ai_questions[0])
        flattened_list = [item for sublist in df[api_column+'-API'].tolist() for item in sublist]
        cluster_beneficiary_data = get_beneficiary_clusters(flattened_list)
    for i in range(len(df)):
        data = {}
        df.fillna('', inplace=True)
        row = df.iloc[i].apply(lambda x: str(x) if isinstance(x, (int,np.integer)) else x)
        for q in questions:
            if q.qtype in ['C','S','R']:
                data[str(q.id)] = [{'C_0_0': str(get_choice_id(row.get(q.text),q.id))}]
            elif q.qtype == "AI":
                ai_creation_key = row.get(api_column+'-API')[0]
                data[str(q.id)] = [{'AI_0_0': ai_creation_key}]
                clusters = str(cluster_beneficiary_data.get(str(ai_creation_key),''))
                
            elif q.qtype == "D" and row.get(q.text):
                data[str(q.id)] = [{'D_0_0': format_date(row.get(q.text))}]#.strftime('%d-%m-%Y')
            elif q.qtype == "AW":
                addr = {}
                clusters = None 
                for idx,l in enumerate(boundary_levels):
                    addr[str(l.code)] = str(boundary_data.get(row.get(l.name,'').lower()))
                    if idx == len(boundary_levels)-1:
                        clusters = str(boundary_data.get(row.get(l.name,'').lower()))
                data[str(q.id)] = [addr]
            elif q.qtype == "GD":
                row_grid_question = Question.objects.filter(active=2,block__survey_id=survey_id,parent=q,is_grid=True)
                column_grid_question = Question.objects.filter(active=2,block__survey_id=survey_id,parent=q,is_grid=False)
                gd_result = []
                for row_grid in row_grid_question:
                    for column_grid in column_grid_question:
                        column_name = f"{q.text}--{row_grid.text}.{column_grid.text}"
                        if column_grid.qtype in ['C','S','R']:
                            gd_result.append({f'C_{row_grid.id}_{column_grid.id}': str(get_choice_id(row.get(column_name),column_grid.id))})
                        elif column_grid.qtype == "D" and row.get(column_name):
                            gd_result.append({f'D_{row_grid.id}_{column_grid.id}': row.get(column_name)})#.strftime('%d-%m-%Y')
                        else:
                            gd_result.append({f'T_{row_grid.id}_{column_grid.id}': row.get(column_name)})
                data[str(q.id)] = gd_result
            else:
                data[str(q.id)] = [{'T_0_0': str(row.get(q.text,''))}]
        if survey.survey_type == 1 and survey.data_entry_level_id == 1: #location based survey
            clusters = row[boundary_level.name]
        creation_key = row.get('Generation Key') or datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid4())
        df.loc[i, 'Generation Key'] = creation_key

        final_result.extend([{
            "answers_array":data,
            "project_id":projects.get(row.get('Project'),'-1'),
            "approved_status": 1,
            "facility_id": "0",
            "beneficiary_id": "0",
            "vn": "","lo": "","la": "",
            "r_uuid": creation_key,
            "last_updated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cluster_id":str(boundary_data.get(clusters,0)),
            "survey_id":str(survey_id),
            "interface":0
                }])
    return final_result


def get_choice_id(name, qid):
    # Query the database for the choice ID based on choice_name
    choice = Choice.objects.filter(text__in=name.split(','), question_id=qid).values_list('id', flat=True)
    # return [','.join(map(str,choice))] if choice else "[]"
    text = ""
    if len(choice) > 1 :
        text = list(choice)
    elif len(choice) == 1:
        text = choice[0]
    return text

def format_date(value):
    if isinstance(value, (datetime, date)):
        return value.strftime('%d-%m-%Y')
    elif isinstance(value, str):
        try:
            parsed_date = datetime.strptime(value, '%Y/%m/%d')
        except ValueError:
            # Try parsing different common date formats
            for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y'):
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Invalid date string: {value}")
        return parsed_date.strftime('%d-%m-%Y')
    else:
        raise TypeError("Value must be a date, datetime, or string")

# Define a function to split strings containing commas and leave lists unchanged
# def process_string(value):
#     try:
#         parsed_list = ast.literal_eval(value)
#         if isinstance(parsed_list, list):
#             return parsed_list#[x.strip().strip("'").strip('"') for x in value.strip('[]').split(',')]
#     except:
#         return value#split(',')

def get_api_column_name(question):
    cache_surveys = load_data_to_cache_survey()
    survey_questions = load_data_to_cache_questions()
    # api question survey name
    lname_que_id = question.api_json.get('lname_que_id').split(',')
    parent_question = survey_questions.get(lname_que_id[0])
    parent_survey_id = parent_question.get('survey_id')
    cache_parent_survey = cache_surveys.get(str(parent_survey_id))

    # unique question text
    unique_ids = RESPONSE_IMPORT['unique_id']
    question_id = unique_ids.get(str(parent_survey_id))
    unique_question_name = survey_questions.get(question_id)
    column = cache_parent_survey.get('name') + "--" +unique_question_name.get('text') 
    return column

def get_beneficiary_clusters(beneficiaries):
    return dict(BeneficiaryResponse.objects.filter(creation_key__in=beneficiaries).values_list('creation_key','address_2'))

# get the schools linked to project
def get_school_based_project(project_district):
    boundary_data = Boundary.objects.get(boundary_level_type_id=2,code=project_district)
    beneficiary_data = [i.response.get('428') for i in JsonAnswer.objects.filter(active=2,survey_id=1,response__address__1__234__2=str(boundary_data.id)) if i.response.get('428')]
    return beneficiary_data

def get_all_role_user(project):
    email_username = list(UserProjectMapping.objects.filter(active=2,project=project,project__partner_mission_mapping__mission_id=2).values_list('user__email',flat=True).exclude(user__email__isnull=True).exclude(user__email__exact='').distinct())
    return email_username