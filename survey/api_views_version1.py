# from workflow.models import WrokflowStateRoleRelation, TransitionCollection, Workflow, TransitionMeta,State
from survey.capture_sur_levels import convert_string_to_date, convert_date_to_string
from django.db import connection
import logging
import time
# from .new_api_response import common_responses_details
# from .new_apis import get_actual_response
# from .new_apis import file_respone_details_v3
from django.utils import timezone
from survey.serializers import *
from django.contrib.auth.models import User
from django.apps import apps
from datetime import datetime, timedelta
# from beneficiary.models import *
# from survey.monkey_patching import *
from uuid import uuid4
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
from survey.models import *
from survey.custom_decorators import *
from django.db import transaction
from application_master.models import *
# from send_mail.views import send_mail as s_mail
# from beneficiary.models import BeneficiaryType, BeneficiaryResponse, BeneficiaryLink
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from survey.serializers import LinkageListingSerializer
# from beneficiary.views import get_serializer_errors
# from configuration_settings.user_location_views import get_user_level,get_higher_level_locations
# from configuration_settings.form_views import save_profile_view,question_based_answers
from ast import literal_eval
# from userroles.serializers import user_setup
# from dashboard.views import famly_info
import json
import ast
import logging
import sys
import traceback
# from projectmanagement.models import Lineitem,ProjectDonor
# from .api_views import *
from cache_configuration.views import *
from django.conf import settings
import pytz
from dateutil import tz
# from configuration_settings.form_views import load_data_to_cache_survey_based_questions,load_data_to_cache_role,load_data_to_cache_transitionmeta
# from send_mail.models import MailTemplate,MailData
from django.db.models import Max
from django.utils.encoding import smart_str


# function required to convert it in utc
def convert__to_localdate(utc_date):
    to_zone = tz.tzlocal()
    localdate = utc_date.astimezone(to_zone).replace(tzinfo=None)
    return localdate

#################################################################################
##################### Optimized version of api_views ############################
#################################################################################


def create_post_log_v2(request, data):

    from mfv_mis.settings import BASE_DIR
    import os
    today_date = datetime.now()
    year = today_date.strftime("%Y")
    dt = today_date.strftime("%d")
    m = today_date.strftime("%m")
    hour = today_date.strftime("%H")
    minute = today_date.strftime("%M")
    new_file_path = '%s/media/logSync/%s/%s/%s' % (BASE_DIR, year, m, dt)
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)
    file_name = "SyncLog" + "-" + year + "-" + m + "-" + dt + ".txt"
    full_filename = os.path.join(BASE_DIR, new_file_path, file_name)
    with open(full_filename, 'a', encoding='utf8') as f:
        f.writelines(
            "\n\n\n==================================================\n\n")
        f.writelines("\nLog Date & Time : " +
                     datetime.now().strftime("%m/%d/%Y, %H:%M:%S")+"hrs")
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()
    return True


@csrf_exempt
@validate_post_method
# @validate_user_version
def add_survey_answers_version_1(request, **kwargs):
    # Implemented bulk create
    # Before start of bulk create
    # Start time st = datetime.now()
    # End time et = datetime.now()
    # Difference diff = et - st

    response, status, error_msg, response_type, message,approved_by,approved_on,submitted_approval = {}, True, '', 0, '',"","",None
    # data = json.loads(request.body.decode('utf-8'))
    data = request.POST
    create_post_log_v2(request, data)
    if kwargs:
        data=kwargs
    user_id = int(data['u_uuid'])
    sync_res = []
    message = "Success"
    
    # Email to store the json_id  
    updated_record_email_ids,response_current_status,role_workflow_dict = {},{},{}
    
    # # Responses list from database for validating the unique check
    # unique_responses = JsonAnswer.objects.filter(survey_id = 70,active=2)

    # code for update the block id in jsonanwer with boundary id
    activity_queries = {
        'ben_activities': "update survey_jsonanswer a set boundary_id = (case when b.address_5 = 0 then null else b.address_5 end) from beneficiary_beneficiaryresponse b where a.cluster ->> 'BeneficiaryResponse'::text = b.creation_key and a.survey_id in (select survey_id from survey_boundary_level_view where beneficiary_type_id is not null and beneficiary_type_id != 11) and a.id in ({0});",
        'people': "UPDATE survey_jsonanswer a SET boundary_id = (CASE WHEN household_ben.address_5 = 0 THEN null ELSE household_ben.address_5 END) FROM beneficiary_beneficiaryresponse people_ben INNER JOIN survey_jsonanswer people_json ON people_ben.json_answer_id = people_json.id INNER JOIN beneficiary_beneficiaryresponse household_ben ON people_json.response->>'16'::text = household_ben.creation_key::text WHERE a.cluster->>'BeneficiaryResponse'::text = people_ben.creation_key AND a.survey_id IN (SELECT survey_id FROM survey_boundary_level_view WHERE beneficiary_type_id = 11) and a.id in ({0});",
        5: "UPDATE survey_jsonanswer a SET boundary_id = (CASE WHEN (a.cluster->>'Boundary'::text) = '0' THEN NULL ELSE (a.cluster->>'Boundary'::text)::INTEGER END) WHERE a.survey_id IN (SELECT survey_id FROM survey_boundary_level_view WHERE beneficiary_type_id IS NULL AND boundary_level_id = 5) and a.id in ({0});",
    }
    survey_boundary_key = 'survey_boundary_level_view'
    # activities = cache.get(settings.INSTANCE_CACHE_PREFIX + survey_boundary_key)
    # if not activities:
        # with connection.cursor() as cursor:
        #     sql_query = """select survey_id,beneficiary_type_id,boundary_level_id from survey_boundary_level_view"""
            # cursor.execute(sql_query)
            # survey_boundary_level = cursor.fetchall()

        # activities = {level: [] for level in activity_queries.keys()}
        # for activity in survey_boundary_level:
        #     try:
        #         if activity[1] and activity[1] != 11:
        #             activities['ben_activities'].append(activity[0])
        #         elif activity[1] == 11:
        #             activities['people'].append(activity[0])
        #         else:
        #             activities[activity[2]].append(activity[0])
        #     except:
        #         pass
        # cache_set_with_namespace(
        #     'SYNC_SURVEY_INFO', survey_boundary_key, activities, 14400)
    resp_ids = {level: [] for level in activity_queries.keys()}
    try:
        if kwargs:
            pushinput = data['pushInput']
        else:
            pushinput = json.loads(data['pushInput'])
        all_input_ben_uuid = [p.get('beneficiary_id','') for p in pushinput if p.get('beneficiary_id') != '0']
        all_input_ben_list =list(JsonAnswer.objects.filter(active=2,creation_key__in =all_input_ben_uuid).values_list('creation_key',flat=True))
        for val in pushinput:
            try:
                app_answer_obj,error_msg = "",""
                answers_list = eval(str(val.get('answers_array')))

                if (not answers_list) or (val.get('beneficiary_id') != '0' and val.get('beneficiary_id') not in all_input_ben_list):
                    error_msg = "Please check answers_array is None." if not answers_list else "Please check beneficiary is not exists."
                    sync_status = 0
                    server_created_date = ""
                    duplicate_status = "0"
                    continue

                cluster_id = val.get('cluster_id')
                user = User.objects.get(id=user_id)
                survey_ids = val.get('survey_id')
                project_id = val.get('project_id', '')
                # response_id = val.get('response_id')
                beneficiary = val.get('beneficiary_id')
                facility = val.get('facility_id')
                r_uuid = val.get('r_uuid')
                last_updated_date = val.get('last_updated_date')
                files_info = val.get('files_info')
                expenses = val.get('expenses')
                submitted_approval = not bool(val.get('approved_status',1)) # 0 - submit for approved; 1 - only submitted
                # =====EXTRA LINE FOR THE DEACTIVATE FEATURE==
                survy = Survey.objects.get(id=int(survey_ids))
                response_created = datetime.strptime(
                    last_updated_date, "%Y-%m-%d %H:%M:%S")
                '''if survey is deactivated before the response submission then those response will be rejected with the status 4'''
                if survy.active == 3 and convert__to_localdate(survy.deactivated_date) < response_created:
                    sync_status = 4
                    server_created_date = ""
                    duplicate_status = "0"

                else:
                    # ============================================
                    response = JsonAnswer.objects.filter(
                        creation_key=r_uuid).first()
                    response_id = response.id if response else None
                    if not response_id:
                        obj = create_app_answer_data_version1(val)
                        app_answer_obj = update_operator_details_version1(
                            val, obj)
                        media_params = {'app_answer_obj': app_answer_obj,
                                        'cluster_id': cluster_id}
                        # create_media_answers(user, **media_params)

                    ans_params = {'answers_list': answers_list, 'app_answer_obj': app_answer_obj, 'cluster_id': cluster_id, 'survey_ids': survey_ids,
                                  'project_id': project_id, 'response_id': response_id, 'beneficiary': beneficiary, 'facility': facility, 'r_uuid': r_uuid,
                                  'last_updated_date': last_updated_date, "response_created_date": response_created}
                    # code start to check the duplicate status for survey household and quid are 1221,1222,1223 for ration id, samagra id and akrspi unique id.
                    duplicate_status = "0"
                    if survey_ids == "70":
                        if "1221" in answers_list:  # ration_id
                            uid = answers_list.get("1221")[0].get("T_0_0")
                            ration_id_count = JsonAnswer.objects.raw(
                                "select * from survey_jsonanswer where survey_id = 70 and lower(trim((response ->> '1221')::varchar))=lower(trim('"+uid+"'::varchar)) and creation_key !='"+r_uuid+"'")
                            if len(list(ration_id_count)) > 0:
                                duplicate_status = "1"
                        elif "1222" in answers_list:  # samagra_id
                            uid = answers_list.get("1222")[0].get("T_0_0")
                            samagra_id_count = JsonAnswer.objects.raw(
                                "select * from survey_jsonanswer where survey_id = 70 and lower(trim((response ->> '1222')::varchar))=lower(trim('"+uid+"'::varchar)) and creation_key !='"+r_uuid+"'")
                            if len(list(samagra_id_count)) > 0:
                                duplicate_status = "1"
                        elif "1223" in answers_list:  # akrspi_unique_id
                            uid = answers_list.get("1223")[0].get("T_0_0")
                            akrspi_unique_id_count = JsonAnswer.objects.raw(
                                "select * from survey_jsonanswer where survey_id = 70 and lower(trim((response ->> '1223')::varchar))=lower(trim('"+uid+"'::varchar)) and creation_key !='"+r_uuid+"'")
                            if len(list(akrspi_unique_id_count)) > 0:
                                duplicate_status = "1"
                    elif survey_ids == "71":
                        uname = answers_list.get("25")[0].get("T_0_0")
                        address5 = answers_list.get("23")[0].get("5")
                        people_count = JsonAnswer.objects.raw("select * from survey_jsonanswer where survey_id = 71 and lower(trim((response ->> '25')::varchar))=lower(trim('" +
                                                              uname+"'::varchar)) and lower(trim((response->'address'->'1'->'23'->>'5')::varchar))=lower(trim('"+address5+"'::varchar)) and creation_key !='"+r_uuid+"'")
                        if len(list(people_count)) > 0:
                            duplicate_status = "1"
                    elif survey_ids == "181":
                        uname = answers_list.get("944")[0].get("T_0_0")
                        address5 = answers_list.get("1288")[0].get("5")
                        institution_count = JsonAnswer.objects.raw("select * from survey_jsonanswer where survey_id = 181 and lower(trim((response ->> '944')::varchar))=lower(trim('" +
                                                                   uname+"'::varchar)) and lower(trim((response->'address'->'1'->'1288'->>'5')::varchar))=lower(trim('"+address5+"'::varchar)) and creation_key !='"+r_uuid+"'")
                        if len(list(institution_count)) > 0:
                            duplicate_status = "1"
                    elif survey_ids == "73":
                        household_uid = answers_list.get("16")[0].get("AI_0_0")
                        household = JsonAnswer.objects.filter(
                            creation_key=household_uid)
                        if household.count() > 1:
                            household_id = household[0].get_beneficiary_object(
                            ).id
                            uname = answers_list.get("636")[0].get("T_0_0")
                            people_count = JsonAnswer.objects.raw("select * from survey_jsonanswer where survey_id = 73 and lower(trim((response ->> '636')::varchar))=lower(trim('" +
                                                                  uname+"'::varchar)) and lower(trim((response ->> '640')::varchar))=lower(trim('"+str(household_id)+"'::varchar)) and creation_key !='"+r_uuid+"'")
                            if len(list(people_count)) > 0:
                                duplicate_status = "1"
                            # code end to check the duplicate status for survey household and quid are 1221,1222,1223 for ration id, samagra id and akrspi unique id.
                    if response_id or duplicate_status == "0":
                        status, res = create_answers_version1(
                            user, response, **ans_params)
                        # if not response_id:
                        #     create_user_for_mediacontent(
                        #         val, survey_ids, res.id)

                        # ######### condition for work flow module ############
                        # # 58 is the json answer content type
                        # role_type = UserRoles.objects.get(user=user).role_type.first()
                        # role_workflow_linkage = WrokflowStateRoleRelation.objects.filter(
                        #     content_type_id=58, active=2).values('state_id', 'role_id')
                        # role_workflow_dict = { item['state_id']: item['role_id'] for item in role_workflow_linkage}
                        # role_based_states = [item['state_id'] for item in role_workflow_linkage if item['role_id'] == role_type.id]
                        # wf = Workflow.objects.get_or_none(content_type_id=58,initial_state_id__in=role_based_states,active=2)
                        # #,initial_state_id__in=role_based_states,file_flow=Question.objects.filter(block__survey=survy,qtype__in=['I','F'],active=2).exists()
                        # file_flow = bool(Question.objects.filter(block__survey=survy,qtype__in=['I','F'],active=2))
                        # survy = Survey.objects.get(id=int(survey_ids))
                        # if wf and bool(survy.survey_type):
                        #     meta_query = {"source_state":wf.initial_state,"workflow":wf, "active":2}
                        #     if submitted_approval:
                        #         meta_query.pop('source_state')
                        #         updated_record_email_ids.update({res.id:[user.email,res,role_type.name]})
                                
                        #     meta = TransitionMeta.objects.filter(**meta_query).order_by('source_state__order')

                        #     #not including the file questions in the survey
                        #     if not file_flow:
                        #         meta = meta.exclude(destination_state_id=6).exclude(source_state_id=6) # 6= account officer state
                        #     #included the file with submitted for approval
                        #     elif file_flow :
                        #         meta = meta.exclude(source_state_id__in=[1,3],destination_state_id__in=[1,3]) # regional role state
                        #     # elif file_flow and submitted_approval :
                        #     #     meta = meta.exclude(destination_state_id=1)
                        #     current_status = wf.initial_state
                        #     for mt in meta:
                        #         status = 0

                        #         if wf.initial_state == mt.source_state and submitted_approval:
                        #             status = 2
                        #             current_status = mt.destination_state
                        #         obj,created = TransitionCollection.objects.update_or_create(source_state=mt.source_state, destination_state=mt.destination_state,
                        #                                                     content_type_id=58, object_id=res.id, 
                        #                                                     defaults={
                        #                                                     "current_state":current_status,
                        #                                                     "status":status ,})
                        #         if created:
                        #             obj.user = user
                        #             obj.role_id = role_workflow_dict.get(mt.source_state.id)
                        #             obj.save()

                        #         response_current_status.update({res.id:current_status})
                        # # if submitted_approval:
                        #     # role_type = user_role.
                        #     # role_based_states = WrokflowStateRoleRelation.objects.filter(role_id__in=role_type).values_list('state_id', flat=True)
                        #     # transition_collection = TransitionCollection.objects.filter(object_id=res_id,current_state_id__in=role_based_states).update(status=2)
                        
                        # # If village level user created the beneficiaries need to get approval from the cluster level user
                        # if not bool(survy.survey_type):# and val.get('approved_status',1) == 2
                        #     # 18 - Village Volunteer
                        #     # 17 - Programme officer
                        #     # 27 - Cluster Incharge
                        #     beneficiary_resp = BeneficiaryResponse.objects.get_or_none(creation_key=res.creation_key)
                        #     # if cluster level user created record it should auto approve
                        #     if beneficiary_resp and role_type.id in [17, 27]:
                        #         beneficiary_resp.approval_status = 2
                        #         beneficiary_resp.approved_by = user
                        #         beneficiary_resp.approved_on = datetime.now()
                        #     elif beneficiary_resp and role_type.id in [18]:
                        #         beneficiary_resp.approval_status = val.get('approved_status',1)
                        #     beneficiary_resp.save()
                        #     res.save()
                        #     approved_by = beneficiary_resp.approved_by.username if beneficiary_resp.approved_by else ''
                        #     approved_on = beneficiary_resp.approved_on.strftime("%Y-%m-%d %H:%M:%S") if beneficiary_resp.approved_on else ''
                        #     # import ipdb;ipdb.set_trace()
                        # ####################################################

                        # json_obj = JsonAnswer.objects.get(id=res_id)
                        if files_info:
                            image_array = file_media_array(
                                files_info, request.FILES, res.id) if files_info else []
                        # vns = val.get('vn')

                        # function for store the expenses data 
                        if expenses:
                            activity_expenses_push(expenses,res,project_id)
                        response_type, status = 1, True
                        sync_status = 2
                        server_created_date = timezone.localtime(res.created).strftime(
                            "%Y-%m-%d %H:%M:%S")
                    else:
                        sync_status = 0
                        server_created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # if not response_id:
                    # code for update the block id for activities
                    # for key, value in activities.items():
                    #     if (int(survey_ids) in value) and (not response_id or not res.boundary_id):
                    #         resp_ids[key].append(res.id) 

            except Exception as e:
                error_msg = str(val['r_uuid'])+' - '+e.args[0]
                logging.error(str(val['r_uuid'])+' - '+error_msg)
                sync_status = 3
                message = "Failed"
                server_created_date = ""
                duplicate_status = "-1"
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_stack = repr(traceback.format_exception(
                    exc_type, exc_value, exc_traceback))
                logging.error(error_stack)
            finally:
                sync_res.append({"r_uuid": val['r_uuid'], "sync_status": sync_status,"s_created": server_created_date, 'error_msg':error_msg, 'duplicate_status': duplicate_status,"approved_by":approved_by,"approved_on":approved_on,})
    except Exception as ex:
        status = False
        message = "Failed"
        obj=None
        error_msg = ex.args[0]
        logging.error(error_msg)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
        logging.error(error_stack)
    response = {'status': status,
                'message': message,
                "sync_res": sync_res,
                "u_uuid": obj.sample_id if obj else "",
                }
    create_post_log_v2(request,response)
    return JsonResponse(response)

# mail passing to the respected userrole which record got submitted for approval
# Input:
    # updated_record_email_ids - {935345: ['progra_sikar@gmail.com', <JsonAnswer: Solar_5HP__sikar_program__935345>]}
    # response_current_status - {935345: <State: Cluster Coordinator>}
    # role_workflow_dict - {1: 27, 2: 17, 3: 4, 6: 33, 5: 34}
    # approval_status - 1 submitted for approval ,0 rejected/only submitted
def submitted_record_mails(updated_record_email_ids,response_current_status,role_workflow_dict,approval_status):
    roles = load_data_to_cache_role()

    # usertype_with_boundary_level = {i.id:i.organizationunit_set.first().organization_level.id for i in roles}
    json_objects = {str(i.id):i for i in JsonAnswer.objects.filter(id__in=updated_record_email_ids.keys())}

    to_email_query = "select distinct STRING_AGG(distinct au.email, ', ') as email_list from userroles_organizationlocation_location locmtm inner join userroles_organizationlocation loc on loc.id = locmtm.organizationlocation_id inner join userroles_userroles uuserrole on loc.user_id = uuserrole.id inner join userroles_userroles_role_type userrole_mtm on userrole_mtm.userroles_id = uuserrole.id inner join auth_user au on au.id = uuserrole.user_id  where boundary_id in (WITH RECURSIVE BoundaryHierarchy AS ( SELECT id, parent_id, 5 AS level FROM masterdata_boundary WHERE id in ({0}) UNION ALL SELECT mb.id, mb.parent_id, bh.level - 1 FROM BoundaryHierarchy bh INNER JOIN masterdata_boundary mb ON mb.id = bh.parent_id ) SELECT id FROM BoundaryHierarchy @@approved_condition)"
    if approval_status in ['1',1]:#1=approved means only next level user role will get email
        to_email_query = to_email_query.replace("@@approved_condition", "WHERE level <= @@user_level")
    to_email_query = to_email_query.replace("@@approved_condition", "")
    for res_id,email_jsonobj in updated_record_email_ids.items():
        state_obj = response_current_status.get(res_id) 
        role_id = role_workflow_dict.get(state_obj.id)
        role_boundary_level = roles.get(str(role_id))[0]['boundary_code'] if roles.get(str(role_id)) else 0
        to_email_query = to_email_query.replace("@@user_level",str(role_boundary_level) )
        # if json_objects.get(str(res_id)).boundary:
        updated_query = to_email_query.format(json_objects.get(str(res_id)).boundary.id)

        to_mail_str = execute_query(connection, updated_query)
        to_mail_str = [(value,) for (value,) in to_mail_str if value is not None]
        if to_mail_str and to_mail_str[0]:
            to_mail_dict = to_mail_str[0][0].split(",")
            send_mail_with_template('Activity Created', email_jsonobj, to_mail_dict,state_obj,approval_status)

# mail passing function for approved/created the activities
def send_mail_with_template(template_name,email_jsonobj,to_users,state_obj,approval_status):
    #Email Subject Format:
    #0 - Activity Name
    #1 - Project Name
    #2 - Record Id

    #Email Content Format:
    #0 - Role Name
    #1 - Submitted User
    #2 - Activity Name
    #3 - Record Id
    #4 - Date of Record Created
    #5 - Activity Description
    #6 - Link to activity
    #7 - Status (approved/rejected)
    #8 - Approved or created user role
    status = 'rejected' if approval_status in ['0',0] else 'approved'
    mail_template = MailTemplate.objects.filter(active=2,template_name=template_name).first()
    # to_ = ['yuvaraj.kharvi@thesocialbytes.com']
    project_name = email_jsonobj[1].survey.get_activity_project()
    mail_subject = mail_template.subject.format(email_jsonobj[1].survey.name, project_name.name if project_name else '',email_jsonobj[1].id)
    html_template = mail_template.content.format(state_obj.label,email_jsonobj[0],email_jsonobj[1].survey.name,email_jsonobj[1].id,email_jsonobj[1].created.strftime("%Y-%m-%d %H:%M:%S"),email_jsonobj[1].survey.voucher_description or '-',f"{settings.INSTANCE_URL}/configuration/activity/{email_jsonobj[1].id}/",status,email_jsonobj[2])
    response = s_mail(to_users,mail_subject,html_template,)
    mail_status = 3 if response['status'] == 200 else 1
    send_data_obj = MailData.objects.create(subject = mail_subject,content = html_template,mail_to = ';'.join([item for item in to_users if item]),
                                        priority = 1,mail_status = mail_status, send_attempt = 1,mail_cc="",mail_bcc="",
                                        template_name = mail_template,error_details = str(response) )


def activity_expenses_push(expense,json_obj,project_id):
    from budgetmanagement.models import BudgetLineitemFY,CoveredAmount
    budgetlineitemfy = BudgetLineitemFY.objects.filter(active=2,lineitem__activity_id=json_obj.survey_id).first()
    mapped_donors = ProjectDonor.objects.filter(project_id=project_id).values_list('donor_id', flat=True)
    for i in mapped_donors:
        cash,kind = eval(expense.get('cash','{}')).get(str(i),'0'),eval(expense.get('kind','{}')).get(str(i),'0')
        if cash not in ['','0'] or kind not in ['','0']:
            obj = CoveredAmount.objects.update_or_create(
                budgetlineitemfy = budgetlineitemfy,
                donor_id = i,
                response_id = json_obj,
                defaults={
                    "covered_amount_cash":cash or 0,
                    "covered_amount_kind":kind or 0,
                }
            )

# def dublicate_unique_id_exists(responses,answers_list):
#     # import ipdb;ipdb.set_trace()
#     uid = 'HRZ1392927'
#     question_ids = [2850,2849,9,10]
#     print("exists" if any(i.response.get(str(id)) == uid for i in res for id in uids_q) else "")
#     return dub

def create_app_answer_data_version1(val):
    # Create App answer object the primary key of this will be tagged
    # to each answer record of one specific survey
    obj = AppAnswerData.objects.create(latitude=val.get('la'),
                                       longitude=val.get('lo'),
                                       version_number=val.get('vn'),
                                       app_version=val.get('av'),
                                       language_id=val.get('l_id'),
                                       imei=val.get('imei'),
                                       survey_id=val.get('t_id'),
                                       mode=val.get('mode'),
                                       part2_charge=val.get('part2_charge'),
                                       f_sy=val.get('f_sy'),
                                       gps_tracker=val.get('gps_tracker'),
                                       survey_status=val.get('survey_status'),
                                       reason=val.get('reason'),
                                       sample_id=val.get('r_uuid') if val.get(
                                           'r_uuid') else str(uuid4()),  # manualy creating uuid
                                       cluster_id=val.get('cluster_id'),
                                       interface=2,
                                       active=0)
    start_date = val.get('sd')
    end_date = val.get('ed')
    created_on = val.get('created_on')
    sp_s_o = val.get('sp_s_o')
    obj.start_date = datetime.strptime(
        start_date, "%Y-%m-%d %H:%M:%S") if start_date else None
    obj.end_date = datetime.strptime(
        end_date, "%Y-%m-%d %H:%M:%S") if end_date else None
    obj.created_on = datetime.strptime(
        created_on, "%Y-%m-%d %H:%M:%S") if created_on else None
    obj.sp_s_o = datetime.strptime(
        sp_s_o, "%Y-%m-%d %H:%M:%S") if sp_s_o else None
    obj.save()
    return obj


def update_operator_details_version1(val, obj):
    operator_details = eval(str(val.get('OperatorDetails')))
    if isinstance(operator_details, dict):
        op_details = dict((k.lower(), v) for k, v in operator_details.items())
        for k, v in op_details.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        obj.network_type = op_details.get('networktype')
        obj.phone_number = op_details.get('phoneno')
        obj.stoken_sent = op_details.get('stoken')
        obj.save()
    return obj


def create_answers_version1(user, response_obj, **ans_params):
    # from beneficiary.views import save_list_view

    insertion_list, qids_list = [], []
    answers_list = ans_params.get('answers_list')
    app_answer_obj = ans_params.get('app_answer_obj')
    cluster_id = ans_params.get('cluster_id')
    key = ans_params.get('cluster_key')
    response_id = ans_params.get('response_id')
    beneficiary = ans_params.get('beneficiary')
    beneficiary_type = ans_params.get('beneficiary_type_id')
    facility_type = int(ans_params.get('facility_type_id')
                        ) if ans_params.get('facility_type_id') else ''
    facility = int(ans_params.get('facility')
                   ) if ans_params.get('facility') else ''
    survey_ids = ans_params.get('survey_ids')
    app_answer_on = ans_params.get('last_updated_date', None)
    response_created_date = ans_params.get('response_created_date', None)
    language_id = ans_params.get('language_id', None)
    creation_key = str(uuid4())
    training_uuid = ans_params.get('training_uuid')
    batch_uuid = ans_params.get('batch_uuid')
    task_uuid = ans_params.get('task_uuid')
    project_id = ans_params.get('project_id')
    child_reference_id = ans_params.get('child_reference_id', '')
    survey = Survey.objects.get(id=int(survey_ids))
    if not child_reference_id:
        questions = Question.objects.filter(active=2, block__survey=survey)
    else:
        parent_question = child_reference_id.split('_')[0]
        questions = Question.objects.filter(parent=parent_question, active=2)
    resp_dict = question_answer_dict(
        questions, answers_list, response_created_date)
    # this to save the child beneficiary address from parent beneficiary using the api question in child beneficiary
    if not survey.questions().filter(qtype='AW').exists() and survey.questions().filter(api_json__is_beneficiary_ques=2).exists():
        address_question = get_address_question(survey)
        ben_ques = survey.questions().get(api_json__is_beneficiary_ques=2)
        if ben_ques:
            benf_id = resp_dict.get(str(ben_ques.id))
            beneficiary_res_obj = BeneficiaryResponse.objects.get(
                creation_key=benf_id)
            benefited_address = beneficiary_res_obj.get_benefited_address()
            resp_dict.update({'address': benefited_address})
    active = ans_params.get('active')
    if survey.survey_type == 0:
        model_name = BeneficiaryResponse
    else:
        model_name = JsonAnswer
    cluster_dict = {}
    if not response_id:
        language_obj = None
        ansobj = JsonAnswer.objects.create(user=user, creation_key=app_answer_obj.sample_id,
                                           survey=survey, response=resp_dict)
        ansobj.app_answer_data = int(app_answer_obj.id)
        ansobj.app_answer_on = app_answer_on if app_answer_on else None
        if language_id:
            language_obj = Language.objects.get_or_none(id=language_id)
        ansobj.language = language_obj
        ansobj.save()
        if survey.survey_type == 0:
            ben_answer = BeneficiaryResponse.objects.create(
                creation_key=app_answer_obj.sample_id, survey=survey)
            ben_answer.beneficiary_type = survey.content_object
            # from projectmanagement.project_views import get_user_partner
            partner_obj = None#get_user_partner(user)
            ben_answer.partner = partner_obj
            ben_answer.json_answer_id = int(ansobj.id)
            address = ansobj.response.get('address')
            if address:
                address_key = address.get('1').keys()
                for i in address_key:
                    address_key = i
                address_data = address.get('1').get(address_key)
                ben_answer.address_1 = address_data.get('1') if address_data and address_data.get(
                    '1') and address_data.get('1') != '' else 0
                ben_answer.address_2 = address_data.get('2') if address_data and address_data.get(
                    '2') and address_data.get('2') != '' else 0
                ben_answer.address_3 = address_data.get('3') if address_data and address_data.get(
                    '3') and address_data.get('3') != '' else 0
                ben_answer.address_4 = address_data.get('4') if address_data and address_data.get(
                    '4') and address_data.get('4') != '' else 0
                ben_answer.address_5 = address_data.get('5') if address_data and address_data.get(
                    '5') and address_data.get('5') != '' else 0
                ben_answer.address_6 = address_data.get('6') if address_data and address_data.get(
                    '6') and address_data.get('6') != '' else 0
                ben_answer.address_7 = address_data.get('7') if address_data and address_data.get(
                    '7') and address_data.get('7') != '' else 0
                ben_answer.address_8 = address_data.get('8') if address_data and address_data.get(
                    '8') and address_data.get('8') != '' else 0
            ben_answer.save()
            if partner_obj:
                cluster_dict = {'partner_creation_key':
                                partner_obj.creation_key,
                                'partner_id': partner_obj.id,
                                'beneficiary_type_id': survey.object_id,
                                'child_reference_id': child_reference_id}
                if child_reference_id:
                    cluster_dict.update({'BeneficiaryResponse': beneficiary})
                ansobj.cluster = cluster_dict
                ansobj.save()
            save_list_view(ben_answer)
        if survey.survey_type == 1:
            '''
                * Below if condition is provided to save the cluster location id of user in cluster column
                * Technically using for Content from cluster form in sphoorthi
                ###1Starts here
            '''
            if survey.extra_config.get('cluster_activity') == 2:
                from userroles.models import UserRoles
                ur_obj = UserRoles.objects.get(user=user)
                b_id = 0
                if ur_obj.get_location_type():
                    boundary_obj = Boundary.objects.get(
                        id=ur_obj.get_location_type()[0])
                    b_id = boundary_obj.parent.id if boundary_obj.parent else 0
                cluster_dict.update({'Cluster_id': b_id})
            # 1 Ends here
            if str(beneficiary) != '0':
                try:
                    beneficiary_object = BeneficiaryResponse.objects.get(
                        creation_key=beneficiary)
                    boundary_id = beneficiary_object.get_beneficiary_address()
                    if boundary_id:
                        cluster_dict.update({'Boundary': str(boundary_id)})
                    else:
                        cluster_dict.update({'Boundary': ""})
                except:
                    pass
                cluster_dict.update({'BeneficiaryResponse': beneficiary})
            elif cluster_id:
                cluster_dict.update({'Boundary': cluster_id})
            if training_uuid:
                try:
                    json_id = JsonAnswer.objects.get_or_none(
                        creation_key=str(training_uuid))
                    ben_uuid = BeneficiaryResponse.objects.get_or_none(
                        json_answer_id=json_id.id)
                    train_uuid = ben_uuid.creation_key
                except:
                    train_uuid = ''
                cluster_dict.update({'Training': train_uuid})
            if facility:
                cluster_dict.update({'Facility': facility})
            if batch_uuid:
                cluster_dict.update({'Batch': batch_uuid})
            if task_uuid:
                cluster_dict.update({'Task': task_uuid})
            if active:
                cluster_dict.update({'active': active})
            if child_reference_id:
                cluster_dict.update({'child_reference_id': child_reference_id})
            if project_id:
                cluster_dict.update({'project_id': int(project_id)})
            ansobj.cluster = cluster_dict
            if cluster_dict.get('project_id') and cluster_dict.get('project_id') == '':
                logger.info('MISSING Project ID ' + str(ansobj))
            ansobj.save()
        app_answer_obj.model_name = str(model_name)
        app_answer_obj.save()
        save_profile_view(ansobj)
    else:
        ansobj = response_obj  # JsonAnswer.objects.get(id=int(response_id))
        ansobj.response = resp_dict
        ansobj.save()
        if survey.survey_type == 0:
            ben_answer = BeneficiaryResponse.objects.get(
                json_answer_id=int(ansobj.id))
            address = ansobj.response.get('address')
            if address:
                address_key = address.get('1').keys()
                for i in address_key:
                    address_key = i
                address_data = address.get('1').get(address_key)
                ben_answer.address_1 = address_data.get('1') if address_data and address_data.get(
                    '1') and address_data.get('1') != '' else 0
                ben_answer.address_2 = address_data.get('2') if address_data and address_data.get(
                    '2') and address_data.get('2') != '' else 0
                ben_answer.address_3 = address_data.get('3') if address_data and address_data.get(
                    '3') and address_data.get('3') != '' else 0
                ben_answer.address_4 = address_data.get('4') if address_data and address_data.get(
                    '4') and address_data.get('4') != '' else 0
                ben_answer.address_5 = address_data.get('5') if address_data and address_data.get(
                    '5') and address_data.get('5') != '' else 0
                ben_answer.address_6 = address_data.get('6') if address_data and address_data.get(
                    '6') and address_data.get('6') != '' else 0
                ben_answer.address_7 = address_data.get('7') if address_data and address_data.get(
                    '7') and address_data.get('7') != '' else 0
                ben_answer.address_8 = address_data.get('8') if address_data and address_data.get(
                    '8') and address_data.get('8') != '' else 0
            ben_answer.save()
            save_list_view(ben_answer)
        save_profile_view(ansobj)
    return (True, ansobj)


#################################################################################
##################### Optimized version of new_api_response #####################
#################################################################################


# @csrf_exempt
# def testing_loop(request):
#     userid = 1568
#     server_date_time = None #res_list[len(res_list)-1]["server_date_time"]
#     loop_count = 1
#     result = [1,2]
#     req = 'POST'
#     while len(result) != 0:
#         print loop_count
#         results = new_responses_list_v1(req,userid,server_date_time)
#         result = results['ResponsesData']
#         res_length = len(result)
#         if res_length == 0:
#             res = {'status': 0,'message': "completed", }
#             return JsonResponse(res)
#         server_date_time = result[res_length-1]["server_date_time"]
#         print server_date_time
#         loop_count +=1
#         # survey_id = [r['survey_id'] for r in result]
#     res = {'status': 2,'message': "Success", }
#     return JsonResponse(res)


@csrf_exempt
def new_responses_list_v1(request):
    if request.method == 'POST':

        user_id = request.POST.get("userid")
        user_role = UserRoles.objects.get(user_id=user_id)
        updatedtime_str = request.POST.get("serverdatetime")
        updatedtime = convert_string_to_date(updatedtime_str)
        partner_obj = UserRoles.objects.get(user_id=int(user_id)).partner
        user_specific_responses = user_setup().get('user_location_responses', 0)
        loc_list = []
        # create_post_log(request,call_type="App",creation_key=creation_key,res_id=None)
        # Add and call it from  setting.py
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V1']['BATCH_SIZE']
        # batch_count =  2 if user_id == "1580" else 150
        t1 = datetime.now()
        if user_specific_responses == 2:
            # user_boundary = list(Boundary.objects.filter(id__in=user_role.get_location_type()).values_list('id',flat=True))
            user_boundary = list(user_role.get_poject_based_location())
            # responses_ids=[]
            if user_id:
                loc_list = [str(i) for i in user_boundary]
            # print(loc_list)

            if len(loc_list) > 0:
                household = JsonAnswer.objects.filter(
                    survey_id=70, response__address__1__633__5__in=loc_list)
                # TODO: WE HAD THE ISSUE OF NANO SECONDS not stored in the SQLITE DB (in CUDDLES???) - NEED TO CHECK HERE.
                if updatedtime:
                    household = household.filter(modified__gt=updatedtime)
                group = JsonAnswer.objects.filter(
                    survey_id=71, response__address__1__23__5__in=loc_list)
                if updatedtime:
                    group = group.filter(modified__gt=updatedtime)
                people = JsonAnswer.objects.filter(
                    survey_id=73, response__address__1__1278__5__in=loc_list)
                if updatedtime:
                    people = people.filter(modified__gt=updatedtime)
                institute = JsonAnswer.objects.filter(
                    survey_id=181, response__address__1__1288__5__in=loc_list)
                if updatedtime:
                    institute = institute.filter(modified__gt=updatedtime)
                if len(block_list) > 0:
                    missed_loc_household = JsonAnswer.objects.filter(
                        survey_id=70, response__address__1__633__5__in=block_list)
                    household = missed_loc_household.union(household)
                    missed_loc_institute = JsonAnswer.objects.filter(
                        survey_id=181, response__address__1__1288__5__in=block_list)
                    institute = missed_loc_institute.union(institute)
                    missed_loc_people = JsonAnswer.objects.filter(
                        survey_id=73, response__address__1__1278__5__in=block_list)
                    people = missed_loc_people.union(people)
                    missed_loc_group = JsonAnswer.objects.filter(
                        survey_id=71, response__address__1__23__5__in=block_list)
                    group = missed_loc_group.union(group)
                household = household.order_by('modified')
                people = people.order_by('modified')
                group = group.order_by('modified')
                # institute = institute.order_by('modified')
                # list of active activity surveys in the survey table

                # TODO: Hardcoded for comparing with old logic, will romoved after testing
                activity_survey_list = Survey.objects.filter(
                    active=2, survey_type=1).values_list('id', flat=True)
                # activity_survey_list = [355,340,342,336,321,337,338,339,343,344]

                # TODO: Returns only activities created by user, need to change to most recent activity for each beneificiary
                #       for selected user location
                # Extended activity surveys

                activity_responses = JsonAnswer.objects.filter(
                    survey_id__in=activity_survey_list, user_id=user_id)
                if updatedtime:
                    activity_responses = activity_responses.filter(
                        modified__gt=updatedtime)
                # activity_responses = activity_responses.order_by('modified')
                res_count = 0
                query1 = household | people | group | institute | activity_responses
                query1 = query1.order_by('modified')
                responses = query1[:batch_count]
                t2 = datetime.now()
                res_list = common_responses_details_v1(
                    responses, partner_obj, user_id)
                responses = query1[:batch_count]
                t2 = datetime.now()
                res_list = common_responses_details_v1(
                    responses, partner_obj, user_id)
                t3 = datetime.now()
                # temp_list =  common_responses_details(responses,partner_obj,user_id)
                # t4 = datetime.now()
                updatedtime_str = updatedtime_str if updatedtime_str else ''
                msg = "user_id(modified)-(rowCount, fetchData, fetchRelated: total): " + str(user_id) + "(" + str(
                    updatedtime_str) + ")" + " - " + str(len(res_list)) + ", " + str(t2-t1)+', '+str(t3-t2)+': '+str(t3-t1)
                # print msg
                # print 'common_responses_details_v1 - '+str(t3-t2)
                # if res_list == temp_list:
                #     print "both are same"
                # else:
                #     print "both are different"
                #     res_file = open("res_data_for_10_records"+str(server_date_time)+".txt","w")
                #     temp_file = open("temp_data_for_10_records"+str(server_date_time)+".txt","w")
                #     res_file.write(str(res_list))
                #     temp_file.write(str(temp_list))
                #     res_file.close()
                #     temp_file.close()
                logging.debug(msg)
            else:
                res_list = []

            # TODO: CHECK IF THIS FLAG IS REQUIRED
            # flag = ""
            # responses = JsonAnswer.objects.filter(id__in=responses_ids)
            # if updatedtime:
            #     updated = convert_string_to_date(updatedtime)
            #     responses = responses.filter(modified__gt=updated)
            #     flag = False
            # if user_setup().get('send-all-responses') == 2:
            #     responses = responses.filter().order_by('modified')
            # else:
            #     responses = responses.filter().order_by('modified')[:150]
            # if res_list:
            res = {'status': 2,
                   'batch_size': batch_count,
                   'current_record_count': len(res_list),
                   'message': "Success",
                   "ResponsesData": res_list, }
            # elif flag == False:
            #     res = {"status": 2,
            #         "message": "Data already sent", }
            # else:
            #     res = {"status": 0,
            #         "message": "No responses for this user", }
        else:
            res = {"status": 0,
                   'batch_size': batch_count,
                   'current_record_count': 0,
                   "message": "Invalid User", }
        return JsonResponse(res)


@csrf_exempt
def new_responses_list_v2(request):
    # get user and based on userid get surveys mapped to user
    # get active survey id
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        user_role = UserRoles.objects.get(user_id=user_id)
        ben_modified_date_str = request.POST.get("ben_modified_date")
        ben_modified_date = convert_string_to_date(ben_modified_date_str)
        hd_modified_date_str = request.POST.get("hd_modified_date")
        hd_modified_date = convert_string_to_date(hd_modified_date_str)
        hd_modified_date_str = convert_date_to_string(hd_modified_date)
        act_modified_date_str = request.POST.get("act_modified_date")
        act_modified_date = convert_string_to_date(act_modified_date_str)
        act_modified_date_str = convert_date_to_string(act_modified_date)
        partner_obj = UserRoles.objects.get(user_id=int(user_id)).partner
        user_specific_responses = user_setup().get('user_location_responses', 0)
        loc_list = []
        # Add and call it from  setting.py
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V1']['BATCH_SIZE']
        # batch_count =  2 if user_id == "1580" else 150
        t1 = datetime.now()
        if user_specific_responses == 2:
            # user_boundary = list(Boundary.objects.filter(id__in=user_role.get_location_type()).values_list('id',flat=True))
            user_boundary = list(user_role.get_poject_based_location())
            # responses_ids=[]
            if user_id:
                loc_list = [str(i) for i in user_boundary]
            if len(loc_list) > 0:
                block_list = []
                for each_loc in loc_list:
                    if request.POST.get('blockids') and each_loc not in request.POST.get('blockids'):
                        block_list.append(each_loc)
                household = JsonAnswer.objects.filter(
                    survey_id=70, response__address__1__633__5__in=loc_list)
                # TODO: WE HAD THE ISSUE OF NANO SECONDS not stored in the SQLITE DB (in CUDDLES???) - NEED TO CHECK HERE.
                if ben_modified_date:
                    household = household.filter(
                        modified__gt=ben_modified_date)
                group = JsonAnswer.objects.filter(
                    survey_id=71, response__address__1__23__5__in=loc_list)
                if ben_modified_date:
                    group = group.filter(modified__gt=ben_modified_date)
                people = JsonAnswer.objects.filter(
                    survey_id=73, response__address__1__1278__5__in=loc_list)
                if ben_modified_date:
                    people = people.filter(modified__gt=ben_modified_date)
                institute = JsonAnswer.objects.filter(
                    survey_id=181, response__address__1__1288__5__in=loc_list)
                if ben_modified_date:
                    institute = institute.filter(
                        modified__gt=ben_modified_date)
                if len(block_list) > 0:
                    missed_loc_household = JsonAnswer.objects.filter(
                        survey_id=70, response__address__1__633__5__in=block_list)
                    household = missed_loc_household | household
                    missed_loc_institute = JsonAnswer.objects.filter(
                        survey_id=181, response__address__1__1288__5__in=block_list)
                    institute = missed_loc_institute | institute
                    missed_loc_people = JsonAnswer.objects.filter(
                        survey_id=73, response__address__1__1278__5__in=block_list)
                    people = missed_loc_people | people
                    missed_loc_group = JsonAnswer.objects.filter(
                        survey_id=71, response__address__1__23__5__in=block_list)
                    group = missed_loc_group | group
                household = household.order_by('modified')
                people = people.order_by('modified')
                group = group.order_by('modified')
                # institute = institute.order_by('modified')
                # list of active activity surveys in the survey table

                # TODO: Hardcoded for comparing with old logic, will romoved after testing
                # activity_survey_list = Survey.objects.filter(active=2, survey_type = 1,id__in=lineitem_obj).values_list('id', flat=True)
                # activity_survey_list = [355,340,342,336,321,337,338,339,343,344]

                # TODO: Returns only activities created by user, need to change to most recent activity for each beneificiary
                #       for selected user location
                # Extended activity surveys
                # removed user_id=user_id in query to get data to all the users
                query1 = household | people | group | institute
                # query1 = household.union(people,group,institute,activity_responses)
                query1 = query1.order_by('modified')
                res_count = 0
                responses = query1[:batch_count]
                t2 = datetime.now()
                res_list = common_responses_details_v1(
                    responses, partner_obj, user_id)
                if len(res_list) == 0:
                    # TODO : address fields to be updated for beneficiary table old records
                    # TODO: raw query to fetch household details filter based res_id and order based on id
                    household_details = """select a.* 
                    from beneficiary_beneficiaryresponse b 
                    inner join survey_jsonanswer a on b.survey_id = 70 and b.address_5 in (""" + ', '.join(loc_list) + """) 
                    and a.cluster->>'BeneficiaryResponse'::text = b.creation_key 
                    and a.survey_id = 321 @@household_details_res_id_cond order by a.id @@LIMITS """

                    household_detail_res_id_cond = ""
                    if hd_modified_date_str:
                        household_detail_res_id_cond = " and a.modified > '" + hd_modified_date_str + "' "
                    household_details = household_details.replace(
                        '@@household_details_res_id_cond', household_detail_res_id_cond)
                    household_details = household_details.replace(
                        '@@LIMITS', " LIMIT "+str(batch_count))
                    # res_id_cond = ""
                    # if household_detail_res_id != 0:
                    #     household_details = household_details.replace('@@res_id_cond', " and modified > "+hd_modified_date)
                    #     household_details = household_details.replace('@@LIMITS', " LIMIT "+str(batch_count))
                    responses = JsonAnswer.objects.raw(household_details)
                    t2 = datetime.now()
                    res_list = common_responses_details_v1(
                        responses, partner_obj, user_id)
                if len(res_list) == 0:
                    project_list = ProjectUserRelation.objects.filter(
                        user__in=[user_role.id]).values_list('project', flat=True)
                    proj_list = ''
                    for i in project_list:
                        proj_list += ",'" + str(i) + "'"
                    proj_list = proj_list[1:]
                    loc_list_str = ''
                    for i in loc_list:
                        loc_list_str += ',' + str(i)
                    loc_list_str = loc_list_str[1:]
                    lineitem_obj = Lineitem.objects.filter(active=2, project__in=project_list).exclude(
                        activity__id=321).values_list('activity', flat=True)
                    lineitem_list_str = ''
                    for i in lineitem_obj:
                        lineitem_list_str += ',' + str(i)
                    lineitem_list_str = lineitem_list_str[1:]
                    # TODO : address fields to be updated for beneficiary table old records
                    # TODO: raw query to fetch household details filter based res_id and order based on id
                    activity_data = """select a.* 
                    from survey_jsonanswer a 
                    inner join beneficiary_beneficiaryresponse b on a.cluster->>'BeneficiaryResponse'::text = b.creation_key 
                    inner join survey_survey s on a.survey_id = s.id
                    and a.survey_id in (""" + lineitem_list_str + """)
                    and b.address_5 in (""" + loc_list_str + """)
                    and a.cluster->>'project_id'::text in (""" + proj_list + """)
                    and s.survey_type = 1
                    and a.created >= '2022-04-01'
                    @@activity_res_id_cond
                    order by a.modified @@LIMITS """
                    activity_res_id_cond = ""


                    if act_modified_date_str:
                        activity_res_id_cond = " and a.modified > '" + act_modified_date_str + "' "
                    activity_data = activity_data.replace(
                        '@@activity_res_id_cond', activity_res_id_cond)
                    activity_data = activity_data.replace(
                        '@@LIMITS', " LIMIT "+str(batch_count))
                    responses = JsonAnswer.objects.raw(activity_data)
                    t2 = datetime.now()
                    res_list = common_responses_details_v1(
                        responses, partner_obj, user_id)

                # if len(res_list) == 0:et_trace()

                #     project_list = ProjectUserRelation.objects.filter(user__in = [user_role.id]).values_list('project',flat=True)
                #     proj_list = []
                #     for i  in project_list:
                #         proj_list.append(str(i))
                #     lineitem_obj = Lineitem.objects.filter(active=2,project__in = project_list).values_list('activity',flat=True)
                #     activity_responses = JsonAnswer.objects.filter(survey_id__in = lineitem_obj,cluster__project_id__in=proj_list)
                #     if res_id:
                #         activity_responses = activity_responses.filter(id__gt=res_id)
                #     print("act",activity_responses.count())
                # activity_responses = activity_responses.order_by('modified')

                t3 = datetime.now()
                # temp_list =  common_responses_details(responses,partner_obj,user_id)
                # t4 = datetime.now()
                # updatedtime_str = updatedtime_str if updatedtime_str else ''
                # msg = "user_id(modified)-(rowCount, fetchData, fetchRelated: total): " + str(user_id) + "(" + str(updatedtime_str) + ")" + " - " + str(len(res_list)) + ", " + str(t2-t1)+', '+str(t3-t2)+': '+str(t3-t1)
                # print msg
                # print 'common_responses_details_v1 - '+str(t3-t2)
                # if res_list == temp_list:
                #     print "both are same"
                # else:
                #     print "both are different"
                #     res_file = open("res_data_for_10_records"+str(server_date_time)+".txt","w")
                #     temp_file = open("temp_data_for_10_records"+str(server_date_time)+".txt","w")
                #     res_file.write(str(res_list))
                #     temp_file.write(str(temp_list))
                #     res_file.close()
                #     temp_file.close()
                # logging.debug(msg)
            else:
                res_list = []

            # TODO: CHECK IF THIS FLAG IS REQUIRED
            # flag = ""
            # responses = JsonAnswer.objects.filter(id__in=responses_ids)
            # if updatedtime:
            #     updated = convert_string_to_date(updatedtime)
            #     responses = responses.filter(modified__gt=updated)
            #     flag = False
            # if user_setup().get('send-all-responses') == 2:
            #     responses = responses.filter().order_by('modified')
            # else:
            #     responses = responses.filter().order_by('modified')[:150]
            # if res_list:
            res = {'status': 2,
                   'batch_size': batch_count,
                   'current_record_count': len(res_list),
                   'message': "Success",
                   "ResponsesData": res_list, }
            # elif flag == False:
            #     res = {"status": 2,
            #         "message": "Data already sent", }
            # else:
            #     res = {"status": 0,
            #         "message": "No responses for this user", }
        else:
            res = {"status": 0,
                   'batch_size': batch_count,
                   'current_record_count': 0,
                   "message": "Invalid User", }
        return JsonResponse(res)

# fetch all results of a raw select query


def execute_query(conn, sql):
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        result = list(cursor.fetchall())
    finally:
        if cursor:
            cursor.close()
    return result

# returns a list of ration_id which are duplicates, that is, used in more than one household response


def get_duplicate_ration_ids(connection):
    st = datetime.now()
    sql_query = "select trim(lower((response ->> '1221')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1221','')::varchar) != '' group by trim(lower((response ->> '1221')::varchar)) having count(*) > 1"
    duplicate_ration_id = execute_query(connection, sql_query)
    duplicate_ration_id = [i[0] for i in duplicate_ration_id]
    et = datetime.now()
    return duplicate_ration_id

# returns a list of samagra_id which are duplicates, that is, used in more than one household response


def get_duplicate_samagra_ids(connection):
    st = datetime.now()
    sql_query = "select trim(lower((response ->> '1222')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1222','')::varchar) != '' group by trim(lower((response ->> '1222')::varchar)) having count(*) > 1"
    duplicate_samagra_id = execute_query(connection, sql_query)
    duplicate_samagra_id = [i[0] for i in duplicate_samagra_id]
    et = datetime.now()
    return duplicate_samagra_id

# returns a list of akrspi_uid which are duplicates, that is, used in more than one household response


def get_duplicate_akrspi_uids(connection):
    st = datetime.now()
    sql_query = "select trim(lower((response ->> '1223')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1223','')::varchar) != '' group by trim(lower((response ->> '1223')::varchar)) having count(*) > 1"
    duplicate_akrspi_uid = execute_query(connection, sql_query)
    duplicate_akrspi_uid = [i[0] for i in duplicate_akrspi_uid]
    et = datetime.now()
    return duplicate_akrspi_uid


def get_duplicate_list(connection, survey_id):
    result = None
    if survey_id == 73:
        with connection.cursor() as cursor:
            sql_query = """select "response.640","response.636" from export_csv_73_0_temp inner join 
            survey_jsonanswer on export_csv_73_0_temp.id=survey_jsonanswer.id and survey_jsonanswer.active=2 
            group by "response.640","response.636" having count(*) > 1"""
            cursor.execute(sql_query)
            result = cursor.fetchall()
    elif survey_id == 71:
        with connection.cursor() as cursor:
            sql_query = """select "response.25","address.7__id__" from export_csv_71_0_temp inner 
            join survey_jsonanswer on export_csv_71_0_temp.id=survey_jsonanswer.id and survey_jsonanswer.active=2 
            group by "response.25","address.7__id__" having count(*) > 1"""
            cursor.execute(sql_query)
            result = cursor.fetchall()
    elif survey_id == 181:
        with connection.cursor() as cursor:
            sql_query = """select "response.944","address.5__id__" 
                from export_csv_181_0_temp inner join survey_jsonanswer on export_csv_181_0_temp.id=survey_jsonanswer.id and 
                survey_jsonanswer.active=2 group by "response.944","address.5__id__" having count(*) > 1"""
            cursor.execute(sql_query)
            result = cursor.fetchall()
    return result


# returns a dict with aw question id for each survey id
# assumes only one AW type question for a survey
def get_aw_questions_dict():
    # TODO: cache aw_questions_dict - 1 day
    # NOTE: cache namespace="SYNC_SURVEY_INFO",key = "aw_questions_dict"
    cache_key = 'aw_questions_dict'
    aw_questions_dict = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if not aw_questions_dict:
        st = datetime.now()
        aw_questions_list = Question.objects.filter(
            qtype='AW').values_list('id', 'block__survey_id')
        aw_questions_dict = {}
        for i in aw_questions_list:
            aw_questions_dict.update({i[1]: i[0]})
        et = datetime.now()
        cache_set_with_namespace('SYNC_SURVEY_INFO', cache_key, aw_questions_dict, settings.CACHES.get(
            "default")['DEFAULT_SHORT_DURATION'])
    return aw_questions_dict


@csrf_exempt
def deactivate_id_list(request):
    if request.method == 'POST':
        updatedtime_str = request.POST.get("serverdatetime")
        updatedtime = convert_string_to_date(updatedtime_str)
        if updatedtime and updatedtime_str <= "2022-08-13 07:16:50.823684":
            json_obj = JsonAnswer.objects.filter(active=0)
            response = {'status': 2, 'data': list(
                json_obj.values_list('id', flat=True))}
        elif updatedtime:
            json_obj = JsonAnswer.objects.filter(
                active=0, modified__gt=updatedtime)
            response = {'status': 2, 'data': list(
                json_obj.values_list('id', flat=True))}
        else:
            response = {'status': 2, 'data': []}
        return JsonResponse(response)

# returns a dict with list of GD and In type question IDS for each survey id


def get_grid_questions_dict():
    # DICT Structure
    # {<surveyID>:<list of gd and in question ids>}
    # Example: {7:[1,2,5]}
    # TODO: cache grid_questions_dict - 1 day
    # NOTE: cache namespace="SYNC_SURVEY_INFO",key = "grid_questions_dict"
    cache_key = 'grid_questions_dict'
    grid_questions_dict = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if not grid_questions_dict:
        st = datetime.now()
        grid_questions_list = Question.objects.filter(
            qtype__in=['GD', 'In'], active=2).values_list('id', 'block__survey_id')
        grid_questions_dict = {}
        for i in grid_questions_list:
            qlist = grid_questions_dict.get(i[1])
            if qlist is None:
                qlist = []
            qlist.append(i[0])
            grid_questions_dict.update({i[1]: qlist})
        et = datetime.now()
        cache_set_with_namespace('SYNC_SURVEY_INFO', cache_key, grid_questions_dict,
                                 settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return grid_questions_dict


def get_beneficiary_aw_meta(connection):
    # DICT Structure
    # {<BenSurveyID>:{"aw_qid":<ben address type question_id>,"ai_qid":<ben AI type question_id to set parent benificiary>,"parent_aw_qid":<ben parents' address type question_id when ben does not directly capture address>}}
    # Example: {73:{"aw_qid":1278,"ai_qid":640,"parent_aw_qid":633}}
    # Above example, even though people survey has a aw type question (1278),
    # the location is identified based on the aw question_id (633) of parent beneificary selected in AI question(640)

    # TODO: cache ben_aw_info - 1 day
    # TODO: Group block is active = 0 and people ai question block is active = 0
    # TODO: is_beneficiary_ques is configured as 0 in the people (73) survey
    # NOTE: cache namespace="SYNC_SURVEY_INFO",key = "ben_aw_info"
    # but as discussed with Giri, it should be 2. We will check this and then plan the change on the config
    cache_key = 'ben_aw_info'
    ben_aw_info = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if not ben_aw_info:
        st = datetime.now()
        sql_query = """select b1.survey_id, b1.aw_id, coalesce(b2.ai_id,0), coalesce(p1.aw_id,0) as pb_aw_id,
                    2 as location_level
            from (select c.id as survey_id, a.id as aw_id 
                    from survey_question a 
                    inner join survey_block b on a.block_id = b.id and a.active = 2 
                    -- and b.active = 2 
                    inner join survey_survey c on c.id = b.survey_id and c.survey_type = 0 and c.active = 2
                    where a.qtype in ('AW','AI')
            ) as b1 
            left outer join (select c.id as survey_id, a.id as ai_id, a.api_json->>'parent_beneficiary_id'::text as p_ben_type
                    from survey_question a 
                    inner join survey_block b on a.block_id = b.id and a.active = 2 
                        -- and b.active = 2 
                    inner join survey_survey c on c.id = b.survey_id and c.survey_type = 0 and c.active = 2
                    where a.qtype = 'AI'
                    and a.api_json->>'is_beneficiary_ques'::text = '2'
            ) as b2 on b1.survey_id = b2.survey_id 
            left outer join (
                select c.id as survey_id, a.id as aw_id, c.object_id
                    from survey_question a 
                    inner join survey_block b on a.block_id = b.id and a.active = 2 
                        -- and b.active = 2 
                    inner join survey_survey c on c.id = b.survey_id and c.survey_type = 0 and c.active = 2
                    where a.qtype = 'AW'
            ) as p1 on p1.object_id::text = b2.p_ben_type"""
        result = execute_query(connection, sql_query)
        ben_aw_info = {}
        for row in result:
            # TODO: remove hardcoding of least location
            ben_aw_info.update({row[0]: {"aw_qid": row[1], "ai_qid": row[2],
                               "parent_aw_qid": row[3], "location_level": row[4]}})
        et = datetime.now()
        cache_set_with_namespace('SYNC_SURVEY_INFO', cache_key, ben_aw_info, settings.CACHES.get(
            "default")['DEFAULT_SHORT_DURATION'])
    return ben_aw_info

# loop through the resposnes list and group responses based on beneficiaries and activities and
# identify the surveys ids in the responses for further use to fetch related details


def prepare_responses_info(responses):
    st = datetime.now()
    ben_survey_in_output = []
    ben_responses_in_output = []
    household_responses_in_output = []
    people_responses_in_output = []
    group_responses_in_output = []
    institution_responses_in_output = []
    act_survey_in_output = []
    ai_ben_ques = []
    act_responses_in_output = []
    beneficiary_survey_ids = [70, 71, 73, 181]
    # group responses and surveys in responses to query for related data
    # print(responses)
    for res in responses:
        if res.survey_id == 70:
            ben_survey_in_output.append(res.survey_id)
            ben_responses_in_output.append(str(res.id))
            household_responses_in_output.append(str(res.id))
        elif res.survey_id == 73:
            ben_survey_in_output.append(res.survey_id)
            ben_responses_in_output.append(str(res.id))
            people_responses_in_output.append(str(res.id))
        elif res.survey_id == 71:
            ben_survey_in_output.append(res.survey_id)
            ben_responses_in_output.append(str(res.id))
            group_responses_in_output.append(str(res.id))
        elif res.survey_id == 181:
            ben_survey_in_output.append(res.survey_id)
            ben_responses_in_output.append(str(res.id))
            institution_responses_in_output.append(str(res.id))
        else:
            if res.survey_id == 335:
                if res.response.get('1289'):
                    ai_ben_ques.append(res.response.get('1289'))
                if res.response.get('1290'):
                    ai_ben_ques.append(res.response.get('1290'))
                if res.response.get('1291'):
                    ai_ben_ques.append(res.response.get('1291'))
            else:
                act_survey_in_output.append(res.survey_id)
                act_responses_in_output.append(str(res.id))
    response_info = {"70": household_responses_in_output, "73": people_responses_in_output,
                     "71": group_responses_in_output, "181": institution_responses_in_output,
                     "ben": ben_responses_in_output, "act": act_responses_in_output, "ai_ben_ques": ai_ben_ques}
    ben_survey_in_output = list(set(ben_survey_in_output))
    act_survey_in_output = list(set(act_survey_in_output))
    et = datetime.now()
    # print "prepare_responses_info - "+str(et-st)
    return ben_survey_in_output, act_survey_in_output, response_info

# fetch the cluster details for the beneficiary responses


def get_beneficiary_creation_keys(ai_ben_ques):
    st = datetime.now()
    ben_creation_key_dict = {}
    query_list = []
    sql_query = """select id, creation_key from beneficiary_beneficiaryresponse 
        where id in (""" + ','.join(ai_ben_ques) + """) """
    result = execute_query(connection, sql_query)
    for row in result:
        ben_creation_key_dict.update({row[0]: row[1]})
    et = datetime.now()
    # print "get_beneficiary_cluster_info - "+str(et-st)
    return ben_creation_key_dict

# fetch the cluster details for the beneficiary responses


def get_beneficiary_cluster_info(response_info, ben_aw_meta, ben_survey_in_output):
    st = datetime.now()
    ben_cluster_data = {}
    query_list = []
    for survey_id in ben_survey_in_output:
        aw_meta = ben_aw_meta.get(survey_id)
        sql_query = ""
        if aw_meta.get("ai_qid") != 0:
            sql_query = """select b1.id as response_id,p1.response #>> ('{ address, 1,' || '""" + str(aw_meta.get("parent_aw_qid")) + """'|| ',' ||'""" + str(aw_meta.get("location_level"))+"""' || '}')::text[] as cluster_id,
                mdb.name as cluster_name
                from survey_jsonanswer b1
                inner join beneficiary_beneficiaryresponse b2 on b1.response #>> ('{' ||'""" + str(aw_meta.get("ai_qid"))+"""' || '}')::text[] =b2.id::text
                inner join survey_jsonanswer p1 on p1.id = b2.json_answer_id
                inner join masterdata_boundary mbd on mbd.id::text = p1.response #>> ('{ address, 1,' ||'""" + str(aw_meta.get("parent_aw_qid")) + """'|| ',' ||'""" + str(aw_meta.get("location_level")) + """'|| '}')::text[]
                where b1.survey_id = """ + str(survey_id) + """ and b1.id in (""" + ','.join(response_info.get(str(survey_id))) + """) """

        else:
            sql_query = """select b1.id as response_id, 
            b1.response #>> ('{ address, 1,' || '"""+str(aw_meta.get("aw_qid"))+"""' || ',' ||'""" + str(aw_meta.get("location_level")) + """'|| '}' )::text[] as cluster_id,
            mbd.name as cluster_name
            from survey_jsonanswer b1
            inner join masterdata_boundary mbd on mbd.id::text = b1.response #>> ('{ address, 1,' ||'"""+str(aw_meta.get("aw_qid"))+"""'|| ',' ||'""" + str(aw_meta.get("location_level"))+"""' || '}')::text[]
            where b1.survey_id = """ + str(survey_id) + """ and b1.id in (""" + ','.join(response_info.get(str(survey_id))) + """)"""
            # select b1.id as response_id,
            # b1.response #>> '{ address, 1, 940, 7}' as cluster_id, mbd.name as cluster_name
            # from survey_jsonanswer b1
            # inner join masterdata_boundary mbd on mbd.id::text = b1.response #>> '{ address, 1, 940, 7}'
            # where b1.survey_id = 71 and b1.id in (92242, 92228, 92225, 92223, 92217)
        query_list.append(sql_query)
        sql_query = ' UNION ALL '.join(query_list)
        result = execute_query(connection, sql_query)
        for row in result:
            ben_cluster_data.update(
                {row[0]: {"cluster_id": row[1], "cluster_name": row[2]}})
    et = datetime.now()
    # print "get_beneficiary_cluster_info - "+str(et-st)
    return ben_cluster_data


def common_responses_details_v1(responses, partner_obj, user_id, user_roles=None):

    res_list = []
    res_activity_boundary_list = []
    activity_boundary_dict = {}
    beneficiary_survey_ids = [70, 71, 73, 181]
    has_households = False
    has_activities = False
    has_beneficiaries = False
    ben_survey_in_output, act_survey_in_output, response_info = prepare_responses_info(
        responses)
    # print('func-act',act_survey_in_output)
    # print('func-response',response_info)
    if 70 in ben_survey_in_output:
        has_households = True
    if len(act_survey_in_output) > 0:
        has_activities = True
    if len(ben_survey_in_output) > 0:
        has_beneficiaries = True

    flag = ""
    if has_activities == True:
        for row in responses:
            if row.cluster and row.cluster.get('Boundary'):
                res_activity_boundary_list.append(row.cluster.get('Boundary'))
        result = Boundary.objects.filter(
            id__in=res_activity_boundary_list).values_list('id', 'name')
        for b in result:
            activity_boundary_dict.update({b[0]: b[1]})
    if has_households == True:
        duplicate_ration_id = get_duplicate_ration_ids(connection)
        duplicate_samagra_id = get_duplicate_samagra_ids(connection)
        duplicate_akrspi_uid = get_duplicate_akrspi_uids(connection)
    # duplicate_people_list = get_duplicate_list(connection,73)
    # duplicate_group_list = get_duplicate_list(connection,71)
    # duplicate_institution_list = get_duplicate_list(connection,181)
    aw_questions_dict = get_aw_questions_dict()
    grid_questions_dict = get_grid_questions_dict()

    sql_query = "select survey_id, boundary_level_type_id from survey_boundary_level_view"
    survey_boundary_list = execute_query(connection, sql_query)
    survey_boundary_dict = [{i[0]:i[1]} for i in survey_boundary_list]

    ben_cluster_data = {}
    if has_beneficiaries:
        ben_aw_meta = get_beneficiary_aw_meta(connection)
        ben_cluster_data = get_beneficiary_cluster_info(
            response_info, ben_aw_meta, ben_survey_in_output)
    ai_ben_creationkey_dict = {}
    if len(response_info.get("ai_ben_ques")) > 0:
        ai_ben_creationkey_dict = get_beneficiary_creation_keys(
            response_info.get("ai_ben_ques"))

    questions_dict = get_questions()
    household_ben_dict = get_household_for_people(response_info)

    # loop through the resposes and set related information/attributes like location, cluster info (beneficiary/boundary details)
    # mark for duplicate ID usage, list of GD and In type questions used, etc
    for res in responses:
        duplicate_status = "0"
        if has_households == True and (res.response.get('1221') in duplicate_ration_id or res.response.get('1222') in duplicate_samagra_id or res.response.get('1223') in duplicate_akrspi_uid):
            duplicate_status = "1"

        address_dict = {}
        if res.response.get('address'):
            address_dict = res.response.get('address').get(
                '1').get(str(aw_questions_dict.get(res.survey_id)))

        grid_inline_questions = []
        if grid_questions_dict.get(res.survey_id):
            grid_inline_questions = list(
                map(int, grid_questions_dict.get(res.survey_id)))

        cluster_beneficiary = ''
        if res.survey_id not in beneficiary_survey_ids and not type(res.cluster) == list:
            cluster_beneficiary = res.cluster.get(
                'BeneficiaryResponse', '') if res.cluster else ''

        cluster_id = None
        cluster_name = None
        if res.survey_id in beneficiary_survey_ids:
            ben_aw_meta_info = ben_aw_meta.get(res.survey_id)
            cluster_info = ben_cluster_data.get(res.id)
            cluster_id = cluster_info.get("cluster_id") if cluster_info else 0
            cluster_name = cluster_info.get(
                "cluster_name") if cluster_info else ''
            # if res.survey_id == 71:
            #     if (res.response.get("620"),int(res.response.get("address").get('1').get('940').get("7"))) in duplicate_group_list:
            #         duplicate_status = "1"
            # elif res.survey_id == 73:
            #     if (res.response.get("640"),res.response.get("636")) in duplicate_people_list:
            #         duplicate_status = "1"
            # elif res.survey_id == 181:
            #     if (res.response.get("944"),int(res.response.get("address").get('1').get('1288').get("5"))) in duplicate_institution_list:
            #         duplicate_status = "1"
        else:
            # print('outer surva')
            cluster_id = res.cluster.get(
                'Boundary') if res.cluster.get('Boundary') else 0
            cluster_name = activity_boundary_dict.get(int(cluster_id))
        # print('surw-in',activity_boundary_dict)

        # training check is not used and hence training_uuid is set to '' as default
        # training_uuid =''

        # TODO: check with Girish
        # lead-caseworker is not a role slug defined in AKRSPI userroles_roletypes so check may be unnessary
        # try:
        #     active = res.cluster['active']
        # except:
        #     if user_roles and 'lead-caseworker' in RoleTypes.objects.filter(id__in=user_roles).values_list('slug',flat=True):
        #         active = res.active if res.lead_user_id ==int (user_id) or not res.lead_user_id else 0
        #     else:
        active = res.active
        # TODO: Check with Girish
        # Non of the survey's seem to have file types.
        # Only 3 responses in survey_responsefile table with irrelavant content types - not sure have to check
        # commented temporarily
        #
        # files_data = file_respone_details(res)
        files_data = []

        # TODO: NO survey has extra_config->share_response = 2
        # if res.survey.extra_config.get('share_response') == 2:
        #     approved_status = 0
        #     if ResponseFiles.objects.filter(content_type=ContentType.objects.get_for_model(res),object_id=res.id).exists():
        #         try:
        #             rf = ResponseFiles.objects.get_or_none(content_type=ContentType.objects.get_for_model(res),object_id=res.id)
        #         except:
        #             rf = None
        #         if rf:
        #             approved_status = 1 if rf.approve == True else 0
        response_dump = get_actual_response_v1(res.response, aw_questions_dict.get(
            res.survey_id), questions_dict, household_ben_dict, ai_ben_creationkey_dict)
        res_list.append({"response_id": res.id,
                        "app_answer_on": datetime.strftime(timezone.localtime(res.app_answer_on), '%Y-%m-%d %H:%M:%S') if res.app_answer_on else '',
                         "bene_uuid": res.creation_key,
                         "l_id": str(res.language.id) if res.language else '1',
                         "survey_id": int(res.survey.id),
                         "cluster_id": int(cluster_id) if cluster_id != None and cluster_id != '' and cluster_id != 'None' else 0,
                         "cluster_name": cluster_name if cluster_name else '',
                         # res.get_beneficiary_object().creation_key if res.get_beneficiary_object() else '',
                         "ben_parent_uuid": res.creation_key,
                         "response_dump": json.dumps(response_dump),
                         "collected_date": datetime.strftime(
                             res.submission_date, '%Y-%m-%d'),
                         "active": active,
                         "server_date_time": datetime.strftime(
                             res.modified, '%Y-%m-%d %H:%M:%S.%f'),
                         'location': address_dict,
                         'cluster_beneficiary': cluster_beneficiary,
                         'training_survey': 0,  # res.training_survey.id if res.training_survey else 0,
                         # str(res.beneficiary_type.get_survey().id) if res.beneficiary_type else "",
                         'training_survey_id': '',
                         'training_uuid': '',  # training_uuid,
                         'grid_inline_questions': grid_inline_questions,
                         'facility_uuid': res.cluster.get('Facility', ''),
                         'batch_uuid': res.cluster.get('Batch', ''),
                         'task_uuid': res.cluster.get('Task', ''),
                         'image_info': res.get_image_info(),
                         'user_id': res.user.id if res.user else '',
                         'child_reference_id': res.cluster.get('child_reference_id', ''),
                         'files_info': files_data,
                         'duplicate_status': duplicate_status,
                         'project_id': res.cluster.get('project_id', 0),
                         })
    return res_list


def get_actual_response_v1(response, aw_question_id, questions_dict, household_ben_dict, ai_ben_creationkey_dict):
    response_dict = {}
    for k, v in response.items():
        try:
            if k == 'address':
                response_dict.update({k: v})
                for qid in v.get('1').keys():
                    q_info = questions_dict.get(qid)
                    if q_info and q_info.get("qtype") != 'AW' and q_info.get("address_question") == True:
                        response_dict.update(
                            {str(qid): v.get('1').get(str(qid))})
                # address_questions = Question.objects.filter(id__in=v.get('1').keys(), address_question=True).exclude(qtype="AW")
                # for i in address_questions:
                #     try:
                #         response_dict.update({str(i.id): v.get('1').get(str(i.id))})
                #     except Exception as e:
                #         print (e.args[0])
            else:
                # if question_info.get('address_question') == False and question_info.get('qtype') == 'AI':
                if k == '640':
                    response_dict.update({k: household_ben_dict.get(v)})
                elif k in ('1290', '1291', '1289'):
                    response_dict.update(
                        {k: ai_ben_creationkey_dict.get(int(v))})
                else:
                    response_dict.update({k: v})
                    if Question.objects.filter(id=k, address_question=False):
                        question = Question.objects.get(id=k)
                        if question.qtype == 'AI':
                            beneficiary_obj = BeneficiaryResponse.objects.get(
                                id=v)
                            if beneficiary_obj.get_answer():
                                response_dict.update(
                                    {k: str(beneficiary_obj.get_answer().creation_key)})
                        else:
                            response_dict.update({k: v})
        except:
            response_dict.update({k: v})
    return response_dict


def get_questions():
    st = datetime.now()
    # TODO: Cache question dict - one day
    # NOTE: cache namespace="SYNC_SURVEY_INFO",key = "questions_dict"
    cache_key = 'questions_dict'
    questions_dict = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if not questions_dict:
        questions_dict = {}
        questions = Question.objects.all()
        for i in questions:
            questions_dict.update(
                {i.id: {"qtype": i.qtype, 'address_question': i.address_question}})
        et = datetime.now()
        cache_set_with_namespace('SYNC_SURVEY_INFO', cache_key, questions_dict, settings.CACHES.get(
            "default")['DEFAULT_SHORT_DURATION'])
    return questions_dict

# Function to fetch the household creation key for people's listed in the response


def get_household_for_people(response_info):
    st = datetime.now()
    household_ben_dict = {}
    people_res_list = response_info.get('73')
    if len(people_res_list) > 0:
        sql_query = """select (a.response ->> '640')::varchar as household_ben_id, b.creation_key as household_creation_key
                    from survey_jsonanswer as a
                    inner join beneficiary_beneficiaryresponse as b on (a.response ->> '640')::varchar = b.id::varchar
                    where a.survey_id = 73 
                    and a.id in ("""+(','.join(people_res_list)) + """)
                    """
        result = execute_query(connection, sql_query)
        for i in result:
            household_ben_dict.update({i[0]: i[1]})
    et = datetime.now()
    # print "get_household_for_people - "+str(et-st)
    return household_ben_dict



@csrf_exempt
@validate_post_method
# @validate_user_version
def response_list_v1_regional(request, **kwargs):
    # get user and based on userid get surveys mapped to user
    # get active survey id
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        user_role = UserRoles.objects.get(user_id=user_id)
        act_modified_date_str = request.POST.get("act_modified_date")
        act_modified_date = convert_string_to_date(act_modified_date_str)
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V3']['BATCH_SIZE']
        loc_list = []

        loc_list_cache_key = "user_project_based_boundary__" + user_id
        loc_list = cache.get(settings.INSTANCE_CACHE_PREFIX + loc_list_cache_key)
        if not loc_list:
            user_boundary = list(user_role.get_poject_based_location())
            if user_id:
                loc_list = [str(i) if i else 0 for i in user_boundary]
            cache_set_with_namespace('RESPONSE_SURVEY_V3', loc_list_cache_key, loc_list, 14400)
            logger.info("## TIME-TRACKER UserID-loc_list::" + str(user_id) + " : " + str(loc_list))

        if len(loc_list) > 0:
            cache_key = 'user_based_surveys' + '-' + user_id
            lineitem_obj = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
            if not lineitem_obj:
                project_list = ProjectUserRelation.objects.filter(
                    user__in=[user_role.id]).values_list('project', flat=True)
                lineitem_obj = list(Lineitem.objects.filter(
                    active=2, project__in=project_list).values_list('activity', flat=True))
                cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, lineitem_obj, 14400)
            boudnary_level_filter = user_role.organization_unit.organization_level_id

            if boudnary_level_filter != 5:
                loc_list = Boundary.objects.filter(id__in=loc_list)
                loc_list = get_higher_level_locations(loc_list, boudnary_level_filter, 5)
            activities = JsonAnswer.objects.filter(survey_id__in=lineitem_obj, boundary_id__in=loc_list).order_by('modified')

            if act_modified_date:
                activities = activities.filter(modified__gt=act_modified_date)
            responses = activities[:batch_count]
            res_list = common_responses_details_regional_v1(responses, user_id)
            res = {'status': 2,
                   'batch_size': batch_count,
                   'current_record_count': len(res_list),
                   'message': "Success",
                   "ResponsesData": res_list, }
        else:
            res_list = []

            res = {'status': 2,
                   'batch_size': batch_count,
                   'current_record_count': len(res_list),
                   'message': "Success",
                   "ResponsesData": res_list, }

        return JsonResponse(res)



def common_responses_details_regional_v1(responses, user_id, user_roles=None):
    res_list,res_activity_boundary_list = [],[]
    beneficiary_survey_ids = [70, 71, 73, 181]
    has_beneficiaries = False
    has_activities = False
    approved_status_dict,activity_status_dict,activity_boundary_dict,rejected_activities={},{},{},[]
    ben_survey_in_output, act_survey_in_output, response_info = prepare_responses_info(responses)
    if len(ben_survey_in_output) > 0:
        has_beneficiaries = True
    if len(act_survey_in_output) > 0:
        has_activities = True
    ben_cluster_data = {}
    if has_activities == True:
        transitions = TransitionCollection.objects.filter(object_id__in=responses.values_list('id',flat=True)).values('object_id','current_state_id')
        activity_approval = {i['object_id']:i['current_state_id'] for i in transitions}
        role_type = UserRoles.objects.get(user_id = user_id).role_type.values_list('id', flat=True)
        role_workflow_linkage = WrokflowStateRoleRelation.objects.filter(content_type_id=58, active=2).values('state_id', 'role_id')
        role_workflow_dict = {item['role_id'] : item['state_id'] for item in role_workflow_linkage}
        # state_dict = {i.id:i.label for i in State.objects.filter(active=2)}
        for row in responses:
            if row.cluster and row.cluster.get('Boundary'):
                res_activity_boundary_list.append(row.cluster.get('Boundary'))
            
            #checking user have permission to edit the activity
            approval_status = 0
            if role_type and activity_approval.get(row.id) == role_workflow_dict.get(role_type[0]):
                approval_status = 1
            approved_status_dict.update({row.id:approval_status})
            activity_status_dict.update({row.id:activity_approval.get(row.id)})
        result = Boundary.objects.filter(
            id__in=res_activity_boundary_list).values_list('id', 'name')

        # Rejected activites list based on remarks        
        rejected_activities = list(Remarks.objects.filter(destination_state_id = role_workflow_dict.get(role_type[0]),action=0, id__in=Remarks.objects.filter(active=2,object_id__in=list(responses.values_list('id', flat=True))).values('object_id').annotate(max_id=Max('id')).values_list('max_id')).values_list('object_id',flat=True))
        
        # rejected_activities = [d['object_id'] for d in activity_remarks if d['destination_state'] == role_workflow_dict.get(role_type[0])]

        for b in result:
            activity_boundary_dict.update({b[0]: b[1]})
        
    if has_beneficiaries:
        ben_aw_meta = get_beneficiary_aw_meta(connection)
        ben_cluster_data = get_beneficiary_cluster_info(
            response_info, ben_aw_meta, ben_survey_in_output)
        
    all_files_data = file_respone_details_v3(responses)
    file_responses = {i.id:i for i in ResponseFiles.objects.filter(active=2,object_id__in=responses.values_list('id'))}
    for res in responses:
        cluster_id = None
        cluster_name = None
        # files_data = file_respone_details(res)

        if res.survey_id in beneficiary_survey_ids:
            cluster_info = ben_cluster_data.get(res.id)
            cluster_id = cluster_info.get("cluster_id") if cluster_info else 0
            cluster_name = cluster_info.get(
                "cluster_name") if cluster_info else ''
        else:
            cluster_id = res.cluster.get(
                'Boundary') if res.cluster.get('Boundary') else 0
            cluster_name = activity_boundary_dict.get(int(cluster_id))
        res_list.append({"response_id": res.id,
                            "app_answer_on": datetime.strftime(timezone.localtime(res.app_answer_on), '%Y-%m-%d %H:%M:%S') if res.app_answer_on else '',
                            "activity_uuid": res.creation_key,
                            "survey_id": int(res.survey_id),
                            "cluster_id": int(cluster_id) if cluster_id != None and cluster_id != '' and cluster_id != 'None' else 0,
                            "cluster_name": cluster_name if cluster_name else '',
                            "response_dump": json.dumps(question_based_answers(res.survey_id,res.response,api=True,file_responses=file_responses)),
                            "active": res.active,
                            "server_date_time": datetime.strftime(
                                res.modified, '%Y-%m-%d %H:%M:%S.%f'),
                            'user_id': res.user_id or '',
                            'files_info': all_files_data.get(res.id,[]),
                            'project_id': res.cluster.get('project_id', 0),
                            # approved_status is used for if the activity is only submited or submitted for approved
                            # based on the logged in user , the record current state is same as role type 
                            'approved_status':approved_status_dict.get(res.id),
                            # activity_status will return the id of record current which state(role)
                            'activity_status':activity_status_dict.get(res.id,''),
                            # rejected key will return 1 if the record is rejected 
                            'rejected':1 if res.id in rejected_activities else 0,
                            })
    return res_list

@csrf_exempt
# @transaction.atomic
def processActivity(request):
    response = {}
    result = []
    # response_current_status = {}
    sync_status,message=2,"Success"
    activity_info = json.loads(request.body.decode('utf-8'))
    for data in activity_info.get('activity_info',[]):
        res = {"active":2}
        try:
            json_object = JsonAnswer.objects.get(creation_key=data.get('response_id'))
            user_id = data.get('userid')
            # to differenciate the benficiary and activity approval request
            if bool(json_object.survey.survey_type):
                survey_questions = load_data_to_cache_survey_based_questions()
                questions = survey_questions.get(str(json_object.survey_id))
                user_role = UserRoles.objects.get_or_none(user_id=user_id)
                role_type = user_role.role_type.values_list('id', flat=True)
                current_state = data.get('current_state')
                role_based_states = WrokflowStateRoleRelation.objects.filter(
                    role_id__in=role_type).values_list('state_id', flat=True)
                transition_collection = TransitionCollection.objects.filter(object_id=json_object.id).order_by('destination_state__order')
                if transition_collection and current_state == transition_collection.first().current_state_id:
                    eval_transitions = transition_collection.filter(status=0,source_state_id__in=role_based_states).order_by('destination_state__order')
                    # custom condition added for jump the transition of cluster cordinator created records
                    # for program manager
                    if 27 in list(UserRoles.objects.get(user=json_object.user).role_type.values_list('id', flat=True)):
                        eval_transitions.filter(role_id=27,destination_state_id=2).update(status=1)

                    # remarks = Remarks.objects.filter(active=2,object_id=id).order_by('created')
                    # 1 means approved - 0 means rejected
                    status = eval_transitions[data.get('status')].id
                    transition_collection.filter(id=status).update(status=2)#done
                    transition_collection.filter(status=0).exclude(id=status).update(status=3)#jumped
                    selected_transition = transition_collection.get(id=status)

                    # role_workflow_linkage = WrokflowStateRoleRelation.objects.filter(
                        # content_type_id=58, active=2).values('state_id', 'role_id')
                    # role_workflow_dict = {item['state_id']: item['role_id'] for item in role_workflow_linkage}
                    cache_key_role_workflow = "role_workflow_dict_key"
                    role_workflow_dict = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key_role_workflow)
                    if not role_workflow_dict:
                        role_workflow_dict = dict(WrokflowStateRoleRelation.objects.filter(content_type_id=58, active=2).values_list('state_id', 'role_id'))
                        cache_set_with_namespace('WORKFLOW',cache_key_role_workflow,role_workflow_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])

                    transition_collection.update(current_state=selected_transition.destination_state)

                    file_flow  = list(filter(lambda x: x['qtype'] in ['I','F'],questions))

                    meta = load_data_to_cache_transitionmeta()
                    meta = {key: value for key, value in meta.items() if value['source_state_id'] == selected_transition.destination_state_id}
                    #not including the file questions in the survey
                    if not file_flow:
                        meta = {key: value for key, value in meta.items() if value['destination_state_id'] != 6}

                    #included the file with cluster cordinator state id
                    elif file_flow and selected_transition.destination_state_id == 1 :#1=cluster cordinator
                        meta = {key: value for key, value in meta.items() if value['destination_state_id'] != 3}

                    # #included the file with regional role state id
                    # elif file_flow and selected_transition.destination_state_id == 3 :#3=regional role
                    #     meta = meta.exclude(destination_state_id=1)
                    
                    work_flow_dict={17:2,27:1}
                    created_user_role = UserRoles.objects.get_or_none(user=json_object.user).role_type.first()
                    if created_user_role and work_flow_dict.get(created_user_role.id):
                        meta = {key: value for key, value in meta.items() if value['workflow_id'] != work_flow_dict.get(created_user_role.id)}
            
                    for mt_id,mt in meta.items():
                        tc = TransitionCollection.objects.update_or_create(content_type_id=58, object_id=json_object.id, source_state_id=mt['source_state_id'], destination_state_id=mt['destination_state_id'],
                                                                        current_state=selected_transition.destination_state, role_id=role_workflow_dict.get(
                                                                            mt['source_state_id']),
                                                                        defaults={
                                                                            "status": 0,
                                                                            "user_id":user_id
                                                                            }
                                                                        )

                        # response_current_status.update({json_object.id:selected_transition.destination_state})
                    submitted_record_mails({json_object.id:[user_role.user.email,json_object,user_role.role_type.first().name]}, {json_object.id:selected_transition.destination_state},role_workflow_dict,data.get('status',1))
                    
                    Remarks.objects.create(creation_key =data.get('remark_uuid'),content_type_id=58,object_id=json_object.id,user_id=user_id,source_state = selected_transition.source_state,destination_state = selected_transition.destination_state,remark=data.get('remark'),action=data.get('status'))
                    
                    #updating the activity modified time to update in app database
                    json_object.save()

                    res['current_status'] = selected_transition.destination_state.id
                    res['source_status'] = selected_transition.source_state.id
                    res['destination_status'] = selected_transition.destination_state.id
                    
                else:
                    sync_status = 3
                    message = 'This activity already updated. Please sync and try again.'
                    res['current_status'] = transition_collection.first().current_state_id if transition_collection else ''
            
            else:
                beneficiary_response = BeneficiaryResponse.objects.get(creation_key=data.get('response_id'))
                # if beneficiary_response.approval_status != 2 and data.get('status') :
                #     beneficiary_response.approval_status = data.get('status')
                # if beneficiary_response.approval_status != 2 and data.get('status') == 2:
                #     beneficiary_response.approved_by_id = user_id
                #     beneficiary_response.approved_on = datetime.now()
                # elif beneficiary_response.approval_status != 2 and data.get('status') == 3:
                #     beneficiary_response.approval_status = 3
                if bool(data.get('status')) and beneficiary_response.approval_status != 2:
                    beneficiary_response.approval_status = 2
                    beneficiary_response.approved_by_id = user_id
                    beneficiary_response.approved_on = datetime.now()
                elif not bool(data.get('status')) and beneficiary_response.approval_status != 2:
                    beneficiary_response.approval_status = 3
                else:
                    sync_status = 3
                    message = 'This beneficiary already approved. Please sync and try again.'

                beneficiary_response.save()
                json_object.save()
                if sync_status != 3:
                    # 141 - beneficiary response 
                    Remarks.objects.create(creation_key = data.get('remark_uuid'),content_type_id=141,object_id=json_object.id,user_id=user_id,remark=data.get('remark'))
                res['current_status'] = beneficiary_response.approval_status
                if beneficiary_response.approved_by:
                    res['approved_by'] = beneficiary_response.approved_by.username
                    res['approved_on'] = datetime.strftime(beneficiary_response.approved_on, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    res['approved_by'] =""
                    res['approved_on'] = ""
                        
            res['sync_status'] = sync_status
            res['message'] = message
            res['remark_uuid'] = data.get('remark_uuid')
            res['response_id'] = data.get('response_id')
        except Exception as e:
            error_msg = data.get('remark_uuid','')+' - '+e.args[0]
            logging.error(data.get('remark_uuid','')+' - '+error_msg)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(
                exc_type, exc_value, exc_traceback))
            logging.error(error_stack)
            res['message'] = f"Failed - {error_msg}"
            res['sync_status'] = 0
            res['remark_uuid'] = data.get('remark_uuid','')
            res['response_id'] = data.get('response_id')
        result.append(res)
    response['status'] = 2
    response['activity_response'] = result
        
    return JsonResponse(response)

def save_list_view(i):
    json_obj = JsonAnswer.objects.get(id=i.json_answer_id)
    survey = json_obj.survey
    try:
        questions_ids = SurveyDisplayQuestions.objects.get(survey=survey,
                                                       display_type='0').questions
    except:
        questions_ids = [quest.id for quest in Question.objects.filter(
            active=2, block__survey_id=survey.id, qtype__in=['S', 'T', 'R', 'C'], parent=None).order_by('question_order')[:3]]
    questions = Question.objects.filter(id__in=questions_ids, block__survey=survey)
    one_response = {'id': i.id, 'survey_id': survey.id,
                    'language_id': 1, 'active': i.active,
                    'creation_key': str(i.creation_key), 'model_name': i.__class__.__name__}
    final_dict = {}
    one_response = update_question_answers(questions, json_obj, one_response)
    final_dict['data'] = one_response
    header_list = [quest.text for quest in questions]
    header_list.insert(0, "id")
    final_dict['header_list'] = header_list
    i.list_view = final_dict
    i.save()
    return None



def question_answer_dict(questions, answers_list, response_created_on=None):
    from .api_views_version1 import convert__to_localdate
    resp_dict = {}
    address_questions = questions.filter(
        address_question=True, active=2).exclude(qtype="AW")
    for ques in questions:
        if response_created_on and ques.active == 3 and convert__to_localdate(ques.deactivated_date) < response_created_on:
            pass
        else:
            try:
                if ques.qtype == 'D':
                    date_str = list(answers_list.get(str(ques.id))[0].values())[
                        0].replace('\\/', '-')
                    date_fmt = date_str.split('-')
                    date_fmt.reverse()
                    date_rev = '%02d' % int(
                        date_fmt[2]) + '-' + '%02d' % int(date_fmt[1]) + '-' + date_fmt[0]
                    resp_dict[ques.id] = date_rev
                elif ques.qtype in ['S', 'R']:
                    #                if ques.is_other_question():
                    data_list = literal_eval(
                        str(list(answers_list.get(str(ques.id))[0].keys())))
                    for kl in data_list:
                        if len(kl.split("_")) == 4:
                            di_dict = resp_dict.get(
                                'other') if resp_dict.get('other') else {}
                            inner_dict = {}
                            inner_dict.update(
                                {kl.split("_")[3]: answers_list.get(str(ques.id))[0].get(kl)})
                            di_dict.update({str(ques.id): inner_dict})
                            resp_dict.update({"other": di_dict})
                        else:
                            resp_dict[str(ques.id)] = str(
                                list(answers_list.get(str(ques.id))[0].values())[0])
    #                else:
    #                    resp_dict[str(ques.id)]=str(answers_list.get(str(ques.id))[0].values()[0])
                elif ques.qtype in ['AW']:
                    ques_dict = {}
                    ques_dict[str(ques.id)] = [dict([a, str(x)] for a,
                                                    x in answers_list.get(str(ques.id))[
                        0].items())][0]
                    try:
                        for address in address_questions:
                            if list(answers_list.get(str(address.id))[0].values())[0]:
                                ques_dict.update({str(address.id): str(
                                    list(answers_list.get(str(address.id))[0].values())[0])})
                    except:
                        pass
                    final_dict = {'1': ques_dict}
                    resp_dict["address"] = final_dict
                elif ques.qtype in ['AI']:
                    data_list = literal_eval(
                        str(list(answers_list.get(str(ques.id))[0].keys())))
                    for kl in data_list:
                        if len(kl.split("_")) == 4:
                            di_dict = resp_dict.get(
                                'other') if resp_dict.get('other') else {}
                            inner_dict = {}
                            inner_dict.update(
                                {kl.split("_")[3]: answers_list.get(str(ques.id))[0].get(kl)})
                            di_dict.update({str(ques.id): inner_dict})
                            resp_dict.update({"other": di_dict})
                        else:
                            # try:
                            #     resp_dict[str(ques.id)] = str(JsonAnswer.objects.get(creation_key=answers_list.get(str(ques.id))[0].get(kl)).get_beneficiary_object().id)
                            # except:
                            resp_dict[str(ques.id)] = str(
                                answers_list.get(str(ques.id))[0].get(kl))
                elif ques.qtype in ['GD', 'In']:
                    ques_final_dict = {}
                    all_question_dict = {}
                    for i in answers_list.get(str(ques.id)):
                        all_question_dict.update(i)
                    response_unique_keys = list(
                        set([item.split('_')[1] for item in all_question_dict.keys()]))
                    for individual_key in response_unique_keys:
                        individual_response = {}
                        for individual_key_content, value in all_question_dict.items():
                            if individual_key == individual_key_content.split("_")[1]:
                                individual_response.update(
                                    {individual_key_content.split("_")[2]: value})
                        ques_final_dict.update(
                            {individual_key: individual_response})
                    resp_dict[str(ques.id)] = ques_final_dict
    #            elif ques.qtype in ['C']:
    #                response = answers_list.get(str(ques.id) , 0)
    #                if response:
    #                    response = response[0]
    #                    data = []
    #                    for key,value in response.items():
    #                        if key == 'C_0_0':
    #                            choice_list_ids = eval(value)
    #                            choice_list_ids = map(str , choice_list_ids)
    #                            data.append({'ids':choice_list_ids})
    #                        else:
    #                            data.append({'text':value})
    #                    resp_dict[str(ques.id)]=data
                else:
                    resp_dict[str(ques.id)] = list(
                        answers_list.get(str(ques.id))[0].values())[0]
            except Exception as e:
                print(ques.id)
    return resp_dict

def get_address_question(survey):
    if survey.is_beneficiary_based_child() == False:
        address_question = survey.questions().get(qtype='AW')
    else:
        address_question = survey.get_parent_beneficiary_address()
    return address_question

def get_user_partner(user_role):
    if user_role:
        partner = user_role.partner
    else:
        partner = None
    return partner

def get_content_language_text(content_object, language):
    text = ''
    try:
        translated_object = LanguageTranslationText.objects.get_or_none(
            content_type=ContentType.objects.get_for_model(content_object), object_id=content_object.id, language=language)
        if translated_object:
            text = translated_object.text
    except:
        text = ''
    return text


def get_choice_text(choice):
    return smart_str(choice.text) if choice else smart_str(choice)


def update_question_answers(questions, json_obj, one_response):
    # from configuration_settings.templatetags.configuration_tags import get_content_language_text
    # from survey.survey_form_newapis import get_choice_text
    language = None
    if json_obj.language:
        language = json_obj.language
    for ques in questions:
        choice_id = json_obj.response.get(str(ques.id))
        if ques.qtype in ['S', 'R']:
            if choice_id:
                choice = Choice.objects.filter(id=choice_id).first()
                one_response[str(ques.text)] = get_choice_text(choice)
                if language and get_content_language_text(choice, language):
                    one_response[str(ques.text)] = get_content_language_text(choice, language)
            else:
                one_response[str(ques.text)] = ''
        elif ques.qtype in ['C']:
            ch_text = ''
            if not type(choice_id) == list:
                choice_id = literal_eval(choice_id)
            for counter, ch in enumerate(choice_id):
                choice = Choice.objects.get_or_none(id=ch)
                if language and get_content_language_text(choice, language):
                    if counter == 0:
                        ch_text = get_content_language_text(choice, language)
                    else:
                        ch_text = ch_text + ',' + get_content_language_text(choice, language)
                else:
                    if counter == 0:
                        ch_text = get_choice_text(choice)
                    else:
                        ch_text = ch_text + ',' + get_choice_text(choice)
            one_response[str(ques.text)] = ch_text
        elif ques.qtype in ['AI']:
            one_response = display_inline_question(ques, json_obj, one_response)
        else:
            one_response[str(ques.text)] = json_obj.response.get(str(ques.id))
    return one_response


def save_profile_view(answer_obj):
    try:
        if answer_obj.survey.survey_type == 0:
            beneficiary_object = BeneficiaryResponse.objects.get(
                json_answer_id=answer_obj.id)
            latest_answer_object = None
        else:
            beneficiary_object = BeneficiaryResponse.objects.get(
                creation_key=answer_obj.cluster.get('BeneficiaryResponse'))
            latest_answer_object = JsonAnswer.objects.filter(cluster__BeneficiaryResponse=str(
                beneficiary_object.creation_key), survey=answer_obj.survey).order_by('-app_answer_on')[:1]
        if (latest_answer_object and str(latest_answer_object[0].id) == str(answer_obj.id)) or answer_obj.survey.survey_type == 0:
            beneficiary_answer_obj = JsonAnswer.objects.get(
                id=beneficiary_object.json_answer_id)
            try:
                beneficiary_questions_ids = SurveyDisplayQuestions.objects.get(survey=beneficiary_object.survey,
                                                                               display_type='0').questions
            except:
                beneficiary_questions_ids = [quest.id for quest in Question.objects.filter(
                    active=2, block__survey_id=answer_obj.survey.id, qtype__in=['S', 'T', 'R'], parent=None).order_by('question_order')[:3]]
            beneficiary_questions = Question.objects.filter(
                id__in=beneficiary_questions_ids, block__survey=beneficiary_object.survey)
            one_response = {}
            update_question_answers(
                beneficiary_questions, beneficiary_answer_obj, one_response)
            try:
                questions_ids = SurveyDisplayQuestions.objects.get(survey=beneficiary_object.survey,
                                                                   display_type='0').questions
            except:
                questions_ids = []
            questions = Question.objects.filter(
                id__in=questions_ids, block__survey=answer_obj.survey).order_by('code')
            update_question_answers(questions, answer_obj, one_response)
            final_dict = {}
            data_dict = {}
            header_list = []
            if beneficiary_object.profile_view.get('data'):
                data_dict = beneficiary_object.profile_view.get('data')
                header_list = beneficiary_object.profile_view.get(
                    'header_list')
            else:
                data_dict = {}
            data_dict.update(one_response)
            final_dict['data'] = data_dict
            [header_list.append(quest.text) for quest in beneficiary_questions]
            [header_list.append(quest.text) for quest in questions]
            final_dict['header_list'] = list(set(header_list))
            beneficiary_object.profile_view = final_dict
            beneficiary_object.save()
    except:
        pass
    return None
