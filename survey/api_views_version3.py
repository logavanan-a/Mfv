from django.db.models import Q,Max
from survey.models import *
from application_master.models import *
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from survey.capture_sur_levels import convert_string_to_date, convert_date_to_string
# from survey.api_views_version1 import common_responses_details_v1
# from survey.api_views_version1 import prepare_responses_info, get_duplicate_ration_ids, get_duplicate_samagra_ids, get_duplicate_akrspi_uids
# from survey.api_views_version1 import get_aw_questions_dict, get_grid_questions_dict, execute_query, get_beneficiary_aw_meta
# from survey.api_views_version1 import get_beneficiary_aw_meta, get_beneficiary_creation_keys, get_household_for_people
# from survey.api_views_version1 import get_questions, get_actual_response_v1, get_beneficiary_cluster_info
from survey.api_views_version1 import get_questions, get_aw_questions_dict, get_grid_questions_dict, execute_query, get_beneficiary_aw_meta
from django.http import JsonResponse
# from django.db.models import Q
# from projectmanagement.models import Lineitem, ProjectUserRelation
from cache_configuration.views import *
import logging
import json
from django.db import connection
from django.utils import timezone
from collections import defaultdict
from datetime import datetime
# from .new_apis import file_respone_details_v3
# from configuration_settings.user_location_views import get_higher_level_locations
# from .serializers import RemarksSerializer,Remarks,ActivityExpensesSerializer
# from workflow.models import TransitionCollection,WrokflowStateRoleRelation,State
# from budgetmanagement.models import CoveredAmount

logger = logging.getLogger(__name__)


@csrf_exempt
def new_responses_list_v3(request):
    # get user and based on userid get surveys mapped to user
    # get active survey id
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        user_role = User.objects.get(id=user_id)
        ben_modified_date_str = request.POST.get("ben_modified_date")
        ben_modified_date = convert_string_to_date(ben_modified_date_str)
        act_modified_date_str = request.POST.get("act_modified_date")
        act_modified_date = convert_string_to_date(act_modified_date_str)
        act_modified_date_str = convert_date_to_string(act_modified_date)
        # partner_obj = UserRoles.objects.get(user_id=int(user_id)).partner
        loc_list = []

        # Add and call it from  setting.py
        # TODO: change to RESPONSES_V3 and add RESPONSES_V3 - batch_size in settings
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V3']['BATCH_SIZE']
        t1 = datetime.now()
        loc_list_cache_key = "user_project_based_boundary__" + user_id
        loc_list = cache.get(settings.INSTANCE_CACHE_PREFIX + loc_list_cache_key)
        if not loc_list:
            # user_boundary = list(user_role.get_poject_based_location())
            # loc_list = [str(i) for i in user_boundary]
            # loc_list=[]
            district_loc_list = list(UserProjectMapping.objects.filter(active=2, user_id=user_id).values_list('project__district_id', flat=True).distinct())
            loc_list_str = list(map(str,district_loc_list))
            loc_list = Boundary.objects.filter(active=2,code__in = loc_list_str,boundary_level_type_id=2).values_list('id',flat=True)
            cache_set_with_namespace('RESPONSE_SURVEY_V3', loc_list_cache_key, loc_list, 14400)
            logger.info("## TIME-TRACKER UserID-loc_list::" + str(user_id) + " : " + str(loc_list))
        if len(loc_list) > 0:
            # boudnary_level_filter = user_role.organization_unit.organization_level_id
            # query_set = {f"address_{boudnary_level_filter}__in": loc_list}
            beneficiaries_json = BeneficiaryResponse.objects.filter(active=2,address_2__in=loc_list).values_list('json_answer_id', flat=True)
            beneficiaries = JsonAnswer.objects.filter(id__in=beneficiaries_json).order_by('modified')
            if ben_modified_date:
                beneficiaries = beneficiaries.filter(modified__gt=ben_modified_date)
            
            responses = beneficiaries[:batch_count]
            logger.info("#############-----------TIME-TRACKER (Beneficiaries-CommonResponse - Start): " + str(datetime.now()))
            res_list = common_responses_details_v3(responses, user_id,user_role)
            logger.info("#############-----------TIME-TRACKER (Beneficiaries-CommonResponse - End): " + str(datetime.now()))
            logger.info("#############----------TIME-TRACKER (Beneficiaries - ResponseCount): " + str(len(res_list)))
            
            if len(res_list) == 0:
                # logger.info("#############TIME-TRACKER (Activities-Start): " + str(datetime.now()))
                # cache_key = 'user_based_surveys' + '-' + user_id
                # lineitem_obj = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
                # if not lineitem_obj:
                #     project_list = ProjectUserRelation.objects.filter(user__in=[user_role.id]).values_list('project', flat=True)
                #     lineitem_obj = list(Lineitem.objects.filter(active=2, project__in=project_list).values_list('activity', flat=True))
                #     location_based_survey = list(Survey.objects.filter(active=2,survey_type=1,data_entry_level_id=1).values_list('id',flat=True))
                #     lineitem_obj += location_based_survey
                #     cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, lineitem_obj, 14400)

                # cache_key = 'user_based_form_surveys'
                # user_based_survey = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
                # if not user_based_survey:
                #     user_based_survey = list(Survey.objects.filter(active=2,survey_type=1,data_entry_level_id=4).values_list('id',flat=True))
                #     cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, user_based_survey, 14400)

                # activities =  JsonAnswer.objects.filter(survey_id__in=lineitem_obj,boundary_id__in = loc_list,submission_date__date__gte=fy_date).order_by('modified')
                # if boudnary_level_filter != 5:
                #     loc_list = Boundary.objects.filter(id__in=loc_list)
                #     loc_list = get_higher_level_locations(loc_list, boudnary_level_filter, 5)

                #current financial year start and end
                # financial_year = get_financial_years()
                
                # project_location_query = Q(survey_id__in=lineitem_obj, boundary_id__in=loc_list)
                # userbased_query = Q(survey_id__in=user_based_survey,user_id=user_id)
                # activities = JsonAnswer.objects.filter(project_location_query | userbased_query,submission_date__date__range=[financial_year['current_financial_start'],financial_year['current_financial_end']]).order_by('modified')
                activities = JsonAnswer.objects.filter(active=2,cluster__BeneficiaryResponse__in = list(beneficiaries_json.values_list('creation_key',flat=True))).exclude(survey__survey_type = 0).order_by('modified')
                if act_modified_date:
                    activities = activities.filter(modified__gt=act_modified_date)
                responses = activities[:batch_count]
                # logger.info("#############----------TIME-TRACKER (Activities-CommonResponse Start): " + str(datetime.now()))
                res_list = common_responses_details_v3(responses, user_id,user_role)
                # logger.info("#############----------TIME-TRACKER (Activities-CommonResponse End): " + str(datetime.now()))
                logger.info("#############----------TIME-TRACKER (Activites - ResponseCount): " + str(len(res_list)))
                # logger.info("#############----------TIME-TRACKER (Activities-End): " + str(datetime.now()))
        else:
            res_list = []

        res = {'status': 2,
                'batch_size': batch_count,
                'current_record_count': len(res_list),
                'message': "Success",
                "ResponsesData": res_list, }

        logger.info("##TIME-TRACKER (End (ResponseCount) - " + user_id +
                    " : " + str(len(res_list)) + "): " + str(datetime.now()))
        return JsonResponse(res)

def get_financial_years():
    import datetime
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    if current_month < 4:
        previous_year = current_year - 1
        current_financial_start = datetime.date(current_year - 1, 4, 1)
        current_financial_end = datetime.date(current_year, 3, 31)
    else:
        previous_year = current_year
        current_financial_start = datetime.date(current_year, 4, 1)
        current_financial_end = datetime.date(current_year + 1, 3, 31)

    return {
        'current_financial_start': current_financial_start.strftime('%Y-%m-%d'),
        'current_financial_end': current_financial_end.strftime('%Y-%m-%d'),
    }


def common_responses_details_v3(responses, user_id,user_role):
    res_list = []
    res_activity_boundary_list = []
    activity_boundary_dict = {}
    # beneficiary_survey_ids = [70, 71, 73, 602]
    all_surveys = load_data_to_cache_survey_objects()
    beneficiary_survey_ids = [i for i,obj in all_surveys.items() if not bool(obj.survey_type)]
    
    has_households = False
    has_activities = False
    has_beneficiaries = False
    approved_status_dict,activity_status_dict,ben_approved_users,ben_approved_on,rejected_activities={},{},{},{},[]
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
    # if has_activities == True:
        # transitions = TransitionCollection.objects.filter(object_id__in=list(responses.values_list('id',flat=True))).values('object_id','current_state_id')
        # activity_approval = {i['object_id']:i['current_state_id'] for i in transitions}
        # role_type = user_role.role_type.values_list('id', flat=True)
        # role_workflow_linkage = WrokflowStateRoleRelation.objects.filter(content_type_id=58, active=2).values('state_id', 'role_id')
        # role_workflow_dict = {item['role_id'] : item['state_id'] for item in role_workflow_linkage}
        # # state_dict = {i.id:i.label for i in State.objects.filter(active=2)}
        # for row in responses:
        #     if row.cluster and row.cluster.get('Boundary'):
        #         res_activity_boundary_list.append(row.cluster.get('Boundary'))
            
            # #checking user have permission to edit the activity
            # approval_status = 0
            # if role_type and activity_approval.get(row.id) == role_workflow_dict.get(role_type[0]):
            #     approval_status = 1

            # approved_status_dict.update({row.id:approval_status})
            # activity_status_dict.update({row.id:activity_approval.get(row.id)})
        # result = Boundary.objects.filter(id__in=res_activity_boundary_list).values_list('id', 'name')

        # # Rejected activites list based on remarks        
        # rejected_activities = list(Remarks.objects.filter(destination_state_id = role_workflow_dict.get(role_type[0]),action=0,id__in=Remarks.objects.filter(active=2,object_id__in=list(responses.values_list('id', flat=True))).values('object_id').annotate(max_id=Max('id')).values_list('max_id')).values_list('object_id',flat=True))
        
        # # rejected_activities = [d['object_id'] for d in activity_remarks if d['destination_state'] == role_workflow_dict.get(role_type[0])]

        # for b in result:
        #     activity_boundary_dict.update({b[0]: b[1]})
        
    # if has_households == True:
    #     duplicate_ration_id = get_duplicate_ration_ids(connection, user_id)
    #     duplicate_samagra_id = get_duplicate_samagra_ids(connection, user_id)
    #     duplicate_akrspi_uid = get_duplicate_akrspi_uids(connection, user_id)
    # duplicate_people_list = get_duplicate_list(connection,73)
    # duplicate_group_list = get_duplicate_list(connection,71)
    # duplicate_institution_list = get_duplicate_list(connection,181)

    aw_questions_dict = get_aw_questions_dict()
    grid_questions_dict = get_grid_questions_dict()

    # sql_query = "select survey_id, boundary_level_type_id from survey_boundary_level_view"
    # survey_boundary_list = execute_query(connection, sql_query)
    # survey_boundary_dict = [{i[0]:i[1]} for i in survey_boundary_list]

    ben_cluster_data = {}
    if has_beneficiaries:
        ben_aw_meta = get_beneficiary_aw_meta(connection)
        ben_cluster_data = get_beneficiary_cluster_info(
            response_info, ben_aw_meta, ben_survey_in_output)

        # beneficiary approval records 
        ben_records = BeneficiaryResponse.objects.filter(json_answer_id__in = responses)
        ben_approved_users = dict(ben_records.values_list('json_answer_id','approved_by__username'))
        for i in ben_records:
            approved_status_dict.update({i.json_answer_id:i.approval_status})
            # ben_approved_users.update({i.json_answer_id:i.approved_by})
            ben_approved_on.update({i.json_answer_id:i.approved_on})
    ai_ben_creationkey_dict = {}
    if len(response_info.get("ai_ben_ques")) > 0:
        ai_ben_creationkey_dict = get_beneficiary_creation_keys(
            response_info.get("ai_ben_ques"))

    questions_dict = get_questions()
    household_ben_dict = get_household_for_people(response_info)


    # activity lists of expenses
    # expense_dict = {}
    # if has_activities == True:
    #     all_covered_amt = CoveredAmount.objects.filter(active=2,response_id__in=responses).values('response_id','donor_id','covered_amount_cash','covered_amount_kind')
    #     expense_dict = {i['response_id']: []for i in all_covered_amt}
    #     for i in all_covered_amt:
    #         # resp_covered_amt = {i['donor_id']:{"covered_amount_cash":str(i['covered_amount_cash']),"covered_amount_kind":str(i['covered_amount_kind'])}}
    #         # resp_covered_amt = {i['donor_id']:{"covered_amount_cash":str(i['covered_amount_cash']),"covered_amount_kind":str(i['covered_amount_kind'])}}
    #         resp_covered_amt = {"cash":{i['donor_id']:str(i['covered_amount_cash'])},"kind":{i['donor_id']:str(i['covered_amount_kind'])}}
    #         expense_dict[i['response_id']].append(resp_covered_amt)
    # loop through the resposes and set related information/attributes like location, cluster info (beneficiary/boundary details)
    # mark for duplicate ID usage, list of GD and In type questions used, etc

    # response file 
    all_files_data = file_respone_details_v3(responses)

    for res in responses:
        # cash = {}
        # kind = {}
        # for i in expense_dict.get(res.id,{}):
        #     cash.update(i.get('cash'))
        #     kind.update(i.get('kind'))
        duplicate_status = "0"
        # if has_households == True and (res.response.get('1221') in duplicate_ration_id or res.response.get('1222') in duplicate_samagra_id or res.response.get('1223') in duplicate_akrspi_uid):
        #     duplicate_status = "1"
        # address_dict = {}
        # if res.response.get('address'):
        #     address_dict = res.response.get('address').get('1').get(str(aw_questions_dict.get(res.survey_id)))
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
        else:
            cluster_id = res.cluster.get(
                'Boundary') if res.cluster.get('Boundary') else 0
            cluster_name = activity_boundary_dict.get(int(cluster_id))
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
        # files_data = []

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
        response_dump = get_actual_response_v3(res.response, aw_questions_dict.get(
            res.survey_id), questions_dict, household_ben_dict, ai_ben_creationkey_dict)
        res_list.append({"response_id": res.id,
                        "app_answer_on": datetime.strftime(timezone.localtime(res.app_answer_on), '%Y-%m-%d %H:%M:%S') if res.app_answer_on else '',
                         "bene_uuid": res.creation_key,
                         "l_id": str(res.language_id) if res.language else '1',
                         "survey_id": int(res.survey_id),
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
                         #  'location': address_dict,
                         'cluster_beneficiary': cluster_beneficiary,
                         'training_survey': 0,  # res.training_survey.id if res.training_survey else 0,
                         # str(res.beneficiary_type.get_survey().id) if res.beneficiary_type else "",
                         'training_survey_id': '',
                         'training_uuid': '',  # training_uuid,
                         'grid_inline_questions': grid_inline_questions,
                         'facility_uuid': res.cluster.get('Facility', ''),
                         'batch_uuid': res.cluster.get('Batch', ''),
                         'task_uuid': res.cluster.get('Task', ''),
                         'image_info': [],#res.get_image_info(),
                         'user_id': res.user_id or '',
                         'child_reference_id': res.cluster.get('child_reference_id', ''),
                         'files_info': all_files_data.get(res.id,[]),
                         'duplicate_status': duplicate_status,
                         'project_id': res.cluster.get('project_id', 0),
                         # approved_status is used for if the activity is only submited or submitted for approved
                         # based on the logged in user , the record current state is same as role type 
                         'approved_status':approved_status_dict.get(res.id),
                         # activity_status will return the id of record current which state(role)
                         'activity_status':activity_status_dict.get(res.id,''),
                         # rejected key will return 1 if the record is rejected 
                         'rejected':1 if res.id in rejected_activities else 0,
                         'expenses':{"cash":"","kind":""},#{"cash":json.dumps(cash),"kind":json.dumps(kind)},
                         'approved_by':ben_approved_users.get(res.id,''),
                         'approved_on':datetime.strftime(ben_approved_on.get(res.id), '%Y-%m-%d %H:%M:%S.%f')if ben_approved_on.get(res.id) else '',
                         })
    return res_list

# loop through the resposnes list and group responses based on beneficiaries and activities and
# identify the surveys ids in the responses for further use to fetch related details


def prepare_responses_info(responses):
    st = datetime.now()
    ben_survey_in_output = []
    ben_responses_in_output = []
    household_responses_in_output = []
    people_responses_in_output = []
    group_responses_in_output = []
    assets_responses_in_output = []
    act_survey_in_output = []
    ai_ben_ques = []
    act_responses_in_output = []
    response_info = defaultdict(list)
    all_surveys = load_data_to_cache_survey_objects()
    beneficiary_survey_ids = [i for i,obj in all_surveys.items() if not bool(obj.survey_type)]
    # beneficiary_survey_ids = [70, 71, 73, 181]
    # group responses and surveys in responses to query for related data
    # print(responses)
    for res in responses:
        if res.survey_id in beneficiary_survey_ids:
            ben_survey_in_output.append(res.survey_id)
            ben_responses_in_output.append(str(res.id))
            response_info[str(res.survey_id)].append(str(res.id))
        # if res.survey_id == 70:
        #     ben_survey_in_output.append(res.survey_id)
        #     ben_responses_in_output.append(str(res.id))
        #     household_responses_in_output.append(str(res.id))
        # elif res.survey_id == 73:
        #     ben_survey_in_output.append(res.survey_id)
        #     ben_responses_in_output.append(str(res.id))
        #     people_responses_in_output.append(str(res.id))
        # elif res.survey_id == 71:
        #     ben_survey_in_output.append(res.survey_id)
        #     ben_responses_in_output.append(str(res.id))
        #     group_responses_in_output.append(str(res.id))
        # elif res.survey_id == 181:
        #     ben_survey_in_output.append(res.survey_id)
        #     ben_responses_in_output.append(str(res.id))
        #     institution_responses_in_output.append(str(res.id))
        else:
            # if res.survey_id == 335:
            #     if res.response.get('1289'):
            #         ai_ben_ques.append(res.response.get('1289'))
            #     if res.response.get('1290'):
            #         ai_ben_ques.append(res.response.get('1290'))
            #     if res.response.get('1291'):
            #         ai_ben_ques.append(res.response.get('1291'))
            # else:
            act_survey_in_output.append(res.survey_id)
            act_responses_in_output.append(str(res.id))
    response_info['ben'] = ben_responses_in_output
    response_info['act'] = act_responses_in_output
    response_info['ai_ben_ques'] = ai_ben_ques
    # response_info = {"70": household_responses_in_output, "73": people_responses_in_output,
    #                  "71": group_responses_in_output, "181": institution_responses_in_output,
    #                  "ben": ben_responses_in_output, "act": act_responses_in_output, "ai_ben_ques": ai_ben_ques}
    ben_survey_in_output = list(set(ben_survey_in_output))
    act_survey_in_output = list(set(act_survey_in_output))
    et = datetime.now()
    # logger.info("##TIME-TRACKER prepare_responses_info - "+str(et-st))
    return ben_survey_in_output, act_survey_in_output, response_info

# returns a list of ration_id which are duplicates, that is, used in more than one household response


def get_duplicate_ration_ids(connection, user_id):
    st = datetime.now()
    cache_key = "duplicate_ration_id__" + user_id
    duplicate_ration_id = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if duplicate_ration_id is None:
        sql_query = "select trim(lower((response ->> '1221')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1221','')::varchar) != '' group by trim(lower((response ->> '1221')::varchar)) having count(*) > 1"
        duplicate_ration_id = execute_query(connection, sql_query)
        duplicate_ration_id = [i[0] for i in duplicate_ration_id]
        cache_set_with_namespace('RESPONSE_SURVEY_V3',
                                 cache_key, duplicate_ration_id, 3600)
    et = datetime.now()
    # logger.info("##TIME-TRACKER get_duplicate_ration_ids - "+str(et-st))
    return duplicate_ration_id

# returns a list of samagra_id which are duplicates, that is, used in more than one household response


def get_duplicate_samagra_ids(connection, user_id):
    st = datetime.now()
    cache_key = "duplicate_samagra_id__" + user_id
    duplicate_samagra_id = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if duplicate_samagra_id is None:
        sql_query = "select trim(lower((response ->> '1222')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1222','')::varchar) != '' group by trim(lower((response ->> '1222')::varchar)) having count(*) > 1"
        duplicate_samagra_id = execute_query(connection, sql_query)
        duplicate_samagra_id = [i[0] for i in duplicate_samagra_id]
        cache_set_with_namespace('RESPONSE_SURVEY_V3',
                                 cache_key, duplicate_samagra_id, 3600)
    et = datetime.now()
    # logger.info("##TIME-TRACKER get_duplicate_samagra_ids - "+str(et-st))
    return duplicate_samagra_id

# returns a list of akrspi_uid which are duplicates, that is, used in more than one household response


def get_duplicate_akrspi_uids(connection, user_id):
    st = datetime.now()
    cache_key = "duplicate_akrspi_uid__" + user_id
    duplicate_akrspi_uid = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
    if duplicate_akrspi_uid is None:
        sql_query = "select trim(lower((response ->> '1223')::varchar)) from survey_jsonanswer where survey_id = 70 and trim(coalesce(response ->> '1223','')::varchar) != '' group by trim(lower((response ->> '1223')::varchar)) having count(*) > 1"
        duplicate_akrspi_uid = execute_query(connection, sql_query)
        duplicate_akrspi_uid = [i[0] for i in duplicate_akrspi_uid]
        cache_set_with_namespace('RESPONSE_SURVEY_V3',
                                 cache_key, duplicate_akrspi_uid, 3600)
    et = datetime.now()
    # logger.info("##TIME-TRACKER get_duplicate_akrspi_uids - "+str(et-st))
    return duplicate_akrspi_uid

# def get_duplicate_list(connection,survey_id):
#     result = None
#     if survey_id == 73:
#         with connection.cursor() as cursor:
#             sql_query = """select "response.640","response.636" from export_csv_73_0_temp inner join
#             survey_jsonanswer on export_csv_73_0_temp.id=survey_jsonanswer.id and survey_jsonanswer.active=2
#             group by "response.640","response.636" having count(*) > 1"""
#             cursor.execute(sql_query)
#             result = cursor.fetchall()
#     elif survey_id == 71:
#         with connection.cursor() as cursor:
#             sql_query = """select "response.620","address.7__id__" from export_csv_71_0_temp inner
#             join survey_jsonanswer on export_csv_71_0_temp.id=survey_jsonanswer.id and survey_jsonanswer.active=2
#             group by "response.620","address.7__id__" having count(*) > 1"""
#             cursor.execute(sql_query)
#             result = cursor.fetchall()
#     elif survey_id == 181:
#         with connection.cursor() as cursor:
#             sql_query = """select "response.944","address.5__id__"
#                 from export_csv_181_0_temp inner join survey_jsonanswer on export_csv_181_0_temp.id=survey_jsonanswer.id and
#                 survey_jsonanswer.active=2 group by "response.944","address.5__id__" having count(*) > 1"""
#             cursor.execute(sql_query)
#             result = cursor.fetchall()
#     return result

# get_aw_questions_dict
# get_grid_questions_dict
# execute_query
# get_beneficiary_aw_meta

# fetch the cluster details for the beneficiary responses


def get_beneficiary_creation_keys(ai_ben_ques):
    st = datetime.now()
    ben_creation_key_dict = {}
    query_list = []
    sql_query = """select id, creation_key from survey_beneficiaryresponse 
        where creation_key in (""" + str(ai_ben_ques)[1:-1] + """) """
    result = execute_query(connection, sql_query)
    for row in result:
        ben_creation_key_dict.update({row[0]: row[1]})
    et = datetime.now()
    # logger.info("##TIME-TRACKER get_beneficiary_cluster_info - "+str(et-st))
    return ben_creation_key_dict

# Function to fetch the household creation key for people's listed in the response


def get_household_for_people(response_info):
    st = datetime.now()
    household_ben_dict = {}
    people_res_list = response_info.get('73',[])
    if len(people_res_list) > 0:
        sql_query = """select (a.response ->> '640')::varchar as household_ben_id, b.creation_key as household_creation_key
                    from survey_jsonanswer as a
                    inner join survey_beneficiaryresponse as b on (a.response ->> '640')::varchar = b.creation_key::varchar
                    where a.survey_id = 73 
                    and a.id in ("""+(','.join(people_res_list)) + """)
                    """
        result = execute_query(connection, sql_query)
        for i in result:
            household_ben_dict.update({i[0]: i[1]})
    et = datetime.now()
    # logger.info("##TIME-TRACKER get_household_for_people - "+str(et-st))
    return household_ben_dict

# get_questions


def get_actual_response_v3(response, aw_question_id, questions_dict, household_ben_dict, ai_ben_creationkey_dict):
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
                    q_info = questions_dict.get(int(k))
                    # if Question.objects.filter(id=k, address_question=False):
                    # question = Question.objects.get(id=k)
                    if q_info is None:
                        logger.info(
                            "TIME-TRACKER questions id missing from questions dict : " + str(k))
                    if q_info and q_info.get("qtype") != 'AW' and q_info.get("address_question") == False:
                        # changed the AI questions to store creationkey of beneficiary instead of the beneficiary id (integer)
                        # hence the if condition is commented
                        # if q_info.get("qtype") == 'AI':
                        #     # beneficiary_obj = BeneficiaryResponse.objects.get(creation_key=v)
                        #     # if beneficiary_obj.get_answer():
                        #     response_dict.update({k:str(beneficiary_obj.get_answer().creation_key)})
                        # else:
                        response_dict.update({k: v})
        except:
            response_dict.update({k: v})
    return response_dict

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
                mbd.name as cluster_name
                from survey_jsonanswer b1
                inner join survey_beneficiaryresponse b2 on b1.response #>> ('{' ||'""" + str(aw_meta.get("ai_qid"))+"""' || '}')::text[] =b2.creation_key::text
                inner join survey_jsonanswer p1 on p1.id = b2.json_answer_id
                inner join application_master_boundary mbd on mbd.id::text = p1.response #>> ('{ address, 1,' ||'""" + str(aw_meta.get("parent_aw_qid")) + """'|| ',' ||'""" + str(aw_meta.get("location_level")) + """'|| '}')::text[]
                where b1.survey_id = """ + str(survey_id) + """ and b1.id in (""" + ','.join(response_info.get(str(survey_id))) + """) """

        else:
            sql_query = """select b1.id as response_id, 
            b1.response #>> ('{ address, 1,' || '"""+str(aw_meta.get("aw_qid"))+"""' || ',' ||'""" + str(aw_meta.get("location_level")) + """'|| '}' )::text[] as cluster_id,
            mbd.name as cluster_name
            from survey_jsonanswer b1
            inner join application_master_district mbd on mbd.id::text = b1.response #>> ('{ address, 1,' ||'"""+str(aw_meta.get("aw_qid"))+"""'|| ',' ||'""" + str(aw_meta.get("location_level"))+"""' || '}')::text[]
            where b1.survey_id = """ + str(survey_id) + """ and b1.id in (""" + ','.join(response_info.get(str(survey_id))) + """)"""
            # select b1.id as response_id,
            # b1.response #>> '{ address, 1, 940, 7}' as cluster_id, mbd.name as cluster_name
            # from survey_jsonanswer b1
            # inner join application_master_boundary mbd on mbd.id::text = b1.response #>> '{ address, 1, 940, 7}'
            # where b1.survey_id = 71 and b1.id in (92242, 92228, 92225, 92223, 92217)
        query_list.append(sql_query)
        sql_query = ' UNION ALL '.join(query_list)
        result = execute_query(connection, sql_query)
        for row in result:
            ben_cluster_data.update(
                {row[0]: {"cluster_id": row[1], "cluster_name": row[2]}})
    et = datetime.now()
    logger.info("##TIME-TRACKER get_beneficiary_cluster_info - "+str(et-st))
    return ben_cluster_data

@csrf_exempt
def activity_remarks(request):
    res={}
    try:
        user_id = request.POST.get("user_id")
        modified_date = request.POST.get("modified_date")
        user_role = UserRoles.objects.get(user_id=user_id)
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V3']['BATCH_SIZE']

        loc_list_cache_key = "user_project_based_boundary__" + user_id
        loc_list = cache.get(settings.INSTANCE_CACHE_PREFIX + loc_list_cache_key)
        if not loc_list:
            user_boundary = list(user_role.get_poject_based_location())
            loc_list = [str(i) for i in user_boundary]
            cache_set_with_namespace('RESPONSE_SURVEY_V3', loc_list_cache_key, loc_list, 14400)
        
        # beneficiries for get the remarks related to beneficiaries
        boudary_level_filter = user_role.organization_unit.organization_level_id
        query_set = {f"address_{boudary_level_filter}__in": loc_list}
        beneficiaries_json = BeneficiaryResponse.objects.filter(**query_set).values_list('json_answer_id', flat=True)

        # Geting the all villages related to the block or other boudary level
        if boudary_level_filter != 5:
            loc_list = Boundary.objects.filter(id__in=loc_list)
            loc_list = get_higher_level_locations(loc_list, boudary_level_filter, 5)
                    
        # Activities list mapped to user
        cache_key = 'user_based_surveys' + '-' + user_id
        lineitem_obj = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
        if not lineitem_obj:
            project_list = ProjectUserRelation.objects.filter(user__in=[user_role.id]).values_list('project', flat=True)
            lineitem_obj = list(Lineitem.objects.filter( active=2, project__in=project_list).values_list('activity', flat=True))
            cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, lineitem_obj, 14400)
        
        
        activities = JsonAnswer.objects.filter(survey_id__in=lineitem_obj, boundary_id__in=loc_list).order_by('modified').values_list('id',flat=True)
        remarks = Remarks.objects.filter(Q(object_id__in=beneficiaries_json) | Q(object_id__in=activities))
        if modified_date:
            remarks = remarks.filter(modified__gt=modified_date)

        remark_data = RemarksSerializer(remarks[:batch_count], many=True)
        res['status'] = 2
        res['remarks'] =remark_data.data
    except:
        res['status'] = 0
        res['remarks'] =[]
    return JsonResponse(res)


def file_respone_details_v3(responses):
    import mimetypes
    file_data_dict = defaultdict(int)
    response_dict = defaultdict(list)
    if responses:
        # 58 JsonAnswer
        for i in ResponseFiles.objects.filter(active=2,content_type_id = 58,object_id__in=responses.values_list('id')):
            response_dict[i.object_id].append(i)

        try:
            for res in responses:
                file_data_list = []
                approved_status=''
                for fl_obj in response_dict.get(res.id,[]):
                    '''
                        * Below if condition is to send approve status of each and every file of response
                        * Technically using for Content from cluster for KHPT/Sphoorthi
                    '''
                    inline_index = ''
                    # if res.survey.extra_config.get('cluster_activity') == 2:
                    #     approved_status = 1 if fl_obj.approve else 0
                    if fl_obj.response_image and os.path.exists(fl_obj.response_image.path):
                        # import ipdb;ipdb.set_trace()
                        file_type_ext = mimetypes.MimeTypes().guess_type(fl_obj.response_image.file.name)[0].split('/')
                        if 'image' in file_type_ext[0] or 'video' in file_type_ext[0]:
                            file_type = file_type_ext[0]
                        else:
                            file_type = file_type_ext[1]
                        if fl_obj.question.parent and fl_obj.question.parent.qtype == 'In':
                            inline_index = fl_obj.index if fl_obj.index else ''
                        file_data_list.append({"unique_id":fl_obj.creation_key,
                                                "capture_time":fl_obj.created.strftime("%Y-%m-%d %H:%M:%S.%f"), 
                                                "path":fl_obj.response_image.name,
                                                "filetype":file_type,"qid":fl_obj.question.id,
                                                "approved_status":approved_status,
                                                "inline_index" : inline_index

                                                })
                file_data_dict[res.id]=file_data_list
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logging.error(error_stack)
    return file_data_dict

