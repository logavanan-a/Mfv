from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from survey.models import *
from rest_framework import generics as g
from survey.custom_decorators import *

# from survey.monkey_patching import *
# from masterdata.models import *
# from beneficiary.models import *
import os,re
from datetime import datetime, timedelta
from django.db.models import Q
from django.apps import apps
from survey.serializers import LabelLanguageTranslationSerializer
from survey.capture_sur_levels import convert_string_to_date
import pytz
# from configuration_settings.user_location_views import user_responses
from django.contrib.auth.models import User
# from survey.serializers import *
# from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection,transaction
from ast import literal_eval
from django.db.models import Q,F
import sys, traceback
import  logging
from django.conf import settings
from collections import defaultdict
from cache_configuration.views import *
import logging

logger = logging.getLogger(__name__)

# from application_master.models import BoundaryLevel


def get_time_difference(tabtime):
    # Returns the time difference the tab time and the current server time
    message, response_type = '', 2
    if tabtime:
        tabtime_obj = datetime.strptime(tabtime, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        diff = current_time - tabtime_obj
        diff_time = divmod(diff.days * 86400 + diff.seconds, 60)
        message = "The server time and tab time is more than " + \
            str(diff_time[0])+" minutes "+str(diff_time[1])+" seconds"
        if diff_time[0] < 10:
            response_type = 1
    else:
        message = "Tab time not sent"
    return {'message': message, 'response_type': response_type}

@csrf_exempt
@validate_user
def applogin(request, **kwargs):
    # User model method get_latest_survey_versions is a method which return
    # survey version with piriodicity (common method)
    response, message, error_msg = {}, '', ''
    if request.method == 'POST' and kwargs.get('status', False):
        tabtime = request.POST.get('tabtime')
        user = kwargs.get('user')
        
        time_data = get_time_difference(tabtime)
        message = time_data.get('message', '')
        response_type = time_data.get('response_type')
        appdetails_obj = AppLoginDetails(user=request.user,
                                         surveyversion=request.POST.get(
                                             'surveyversion'),
                                         lang_code=request.POST.get(
                                             'lang_code'),
                                         tabtime=request.POST.get('tabtime')
                                         if request.POST.get('tabtime') else None,
                                         sdc=request.POST.get('sdc')
                                         if request.POST.get('sdc') else 0,
                                         itype=request.POST.get('ltype'),
                                         version_number=request.POST.get('version_number'))
        appdetails_obj.save()
        # userrole_obj = UserRoles.objects.get(user=user)
        # role_typ = userrole_obj.role_type.all()[0].id
        # role_nme = userrole_obj.role_type.all()[0].name
#        role_names = [i.name.lower() for i in userrole_obj.role_type.all()]
#        app_roles = ['community organizer','data entry operator','ceo','vertical specialist', 'field staff', 'master trainer', 'field level officer','development officer','case worker','team lead','director','issac']

        # version_update = VersionUpdate.objects.filter().latest('id')
        # updated_link = user_setup().get('updated_link', "")
        updateapk = {"forceUpdate": "False",
                     "appVersion": 0,
                     "updateMessage": "New update available, download from playstore",
                     "link": ""}
        # if userrole_obj.role_type.filter(app_login=True).exists():

        response = {
            'message': "Logged in successfully",
            'uId': user.id,
            'first_name': '{} {}'.format(user.first_name, user.last_name),
            'role_type': 0,
            'role_name': "",
            'partner_id': 0,
        }
        # elif [i.name.lower() for i in userrole_obj.role_type.all()] in ['data center cordinator', 'admin']:
        #     message = "District Coordinator or admin Logged in"
        # response = {
        #     'message': message,
        #     'uId': user.id,
        #     'role_type': 0,
        #     'role_name': "",
        #     'partner_id': 0,
        # }
        # else:
        # response = {
        #     'message': 'Please contact administrator.',
        #     'status': 0,
        #     'uId': 0,
        #     'role_type': 0,
        #     'role_name': "",
        #     'partner_id': 0,
        #     'response_type': 0,
        # }
        response.update(
            {'updateAPK': updateapk, 'activeStatus': 2, 'forceLogout': 0, })
    else:
        response_type = 0
        error_msg = kwargs.get('error_msg', '')
        response.update({'message': error_msg, 'status': 0,'activeStatus':kwargs.get('activeStatus'),'uId':0})
    response.update({'responseType': response_type, 'updates': 60})
    return JsonResponse(response)


@csrf_exempt
def questionlist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")
        

        quest_list = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        questions = Question.objects.filter().select_related('block','block__survey')

        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            questions = questions.filter(modified__gt=updated)
            flag = False
        questions = questions.filter().order_by('modified')[:100]
        qtype_dict = {'N': 0, 'T': 1, 'S': 6, 'R': 4, 'C': 2, 'D': 5,
                      'G': 7, 'I': 8, 'AW': 9, 'Cl': 3, 'GD': 14, 'In': 16,
                      'AI': 10,'AF':17,'F':18,'TM':19}
        for quest in questions:
            quest.api_json.update({"editable":quest.is_editable})

            if (quest.parent == None and quest.is_grid == False) or (quest.parent != None and quest.is_grid == True):
                quest_list.append({'id': int(quest.id),
                                   'question_type':quest.qtype,
                                   'question_code': int(quest.code),
                                   'answer_type': qtype_dict.get(quest.qtype),
                                   "survey_id": int(quest.block.survey.id),
                                   "block_id": int(quest.block.id),
                                   "sub_question": quest.parent.id if quest.parent else 0,
                                   "question_text": quest.text,
                                   "help_text": quest.help_text,
                                   'instruction_text': "",
                                   "active": quest.active,
                                   "language_id": 1,
                                   "mandatory": int(quest.mandatory),
                                   "question_order": int(quest.question_order) if quest.question_order else 0,
                                   "validation":  quest.get_question_validation() if quest.get_question_validation() else "" ,
    #                               "validation": "",
                                   "image_path": "",
                                   "answer": quest.qtype if (quest.is_grid == False and quest.parent == None) else 'N',
                                   "keyword": quest.api_qtype,
                                   'updated_time': datetime.strftime(quest.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                   'extra_column1': "English",
                                   'extra_column2': 0,
                                   'short_text': "",
                                   'is_attendance_question':quest.training_config.get('is_attendence_question') if quest.training_config.get('is_attendence_question') else 0,
                                   'display_as_name':quest.display_has_name,
                                   'question_json': quest.api_json, "question_id":
                                       quest.api_json.get('question_id', 0),
                                   "parent_beneficiary_id": quest.api_json.get(
                                       'parent_beneficiary_id', 0),
                                   'code_display': str(quest.code_display) if quest.code_display  else '0',
                                #    'individual_qid': quest.reference_question_id or 0 ,
                                #    'editable':int(quest.is_editable),
                                   # if is_code_display is 1 then display the code_display
                                   #"display_as_code": user_setup().get("is_code_display") if user_setup().get("is_code_display") else 0 
                                   })
        if quest_list:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Question": quest_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No questions tagged for this user", }
        return JsonResponse(res)



@csrf_exempt
def choicelist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")
        questions = []
        ch_list = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        choice = Choice.objects.all().select_related('question','question__block','question__block__survey').prefetch_related('skip_question')
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            choice = choice.filter(modified__gt=updated)
            flag = False
        choice = choice.filter().order_by('modified')[:100]
        for ch in choice:
            skip_quest = ""
            if ch.skip_question.all():
                val = [str(i) for i in sorted(list(ch.skip_question.values_list('id',flat=True)))]
                val = ",".join(val)
            elif ch.code == -1:
                val = str(ch.code)
            else:
                val = ""
            ch_list.append({'id': int(ch.id),
                            'question_pid': int(ch.question.id),
                            # 'option_code': str(ch.uuid) if user_setup().get('send_choice_code_as_uuid', 0) == 2 else str(ch.code),
                            "option_flag": 1,
                            "skip_code": val,
                            "validation": "",
                            "order":int(ch.choice_order) if ch.choice_order else 0 ,
                            "option_text": ch.text,
                            "active": ch.active,
                            "language_id": 1,
                            "survey_id": int(ch.question.block.survey.id),
                            "image_path": "",
                            "is_answer": "true",
                            'updated_time': datetime.strftime(ch.modified, '%Y-%m-%d %H:%M:%S.%f'),
                            'extra_column1': "",
                            'extra_column2': 0,
                            'assessment_pid': int(ch.question.id),
                            'is_correct_choice':ch.config.get('is_correct_choice') if ch.config.get('is_correct_choice') else 0,
                            'Rule_engine': ch.get_text_choices_rule_engine(),
                            'other_choice': ch.is_other_choice,
                            'code_display': str(ch.code_display) if ch.code_display  else '0',
                            'score':float(ch.score) if ch.score else 0,
                            'locations': "",#','.join(map(str,ch.boundary.all().values_list('id',flat=True)))  if ch.boundary.all()  else "" ,
                            })
                            #"display_as_code": user_setup().get("is_code_display") if user_setup().get("is_code_display") else 0,
        if ch_list:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Options": ch_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No choices tagged for this user", }
        return JsonResponse(res)

@csrf_exempt
def blocklist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")

        blocks = []
        flag = ""
        updatedtime = request.POST.get("updatedtime")
        bl = Block.objects.all()
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            bl = bl.filter(modified__gt=updated)
            flag = False
        bl = bl.filter().order_by('modified')[:100]
        for j in bl:
            blocks.append({'id': j.id,
                           'block_code': str(j.code) if j.code else "",
                           'survey_id': j.survey.id,
                           'block_order': j.block_order if j.block_order else 0,
                           'block_name': j.name,
                           'active': j.active,
                           'language_id': 1,
                           'updated_time': datetime.strftime(j.modified, '%Y-%m-%d %H:%M:%S.%f'),
                           'extra_column1': "",
                           'extra_column2': 0,
                           })
        if blocks:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Block": blocks, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No Blocks tagged for this user", }
        return JsonResponse(res)

def get_latest_survey_versions(user_id):
    version_updates = []
    user = User.objects.get(id=user_id)
    user_level = 2#get_user_level(user)
    # userrole = UserRoles.objects.filter(user__id=int(user_id))
    survey_list = Survey.objects.filter(active=2).order_by('survey_order')
    version_updates = []
    # all_survey_location = get_all_survey_location(survey_list)
    #updated filter questions 
    filter_questions = list(SurveyDisplayQuestions.objects.filter(active=2).values_list('survey_id', 'display_type','questions'))
    order_levels, labels ="level1,level2","State,District"#user_survey_level_labels_v3(survey_list, user_level)

    all_beneficiary_ids, all_beneficiary_type = get_beneficiary_location_details_v3(user_level, survey_list)
    for i in survey_list:
        generalized = True
        description = ''
        display_name = ''
        display_in_app = 2
        plimit = {1: 45, 2: 60, 3: 365, 4: 365, 5: 365}.get(int(1), 0)
        display_in_training = 0
        if i.survey_type == 0:
            ben_obj = i.get_beneficiary_type()
            if ben_obj.is_admin_type:
                display_in_app = 0
            if ben_obj.is_training_type:
                display_in_training = 2
            if ben_obj.is_training_module:
                category_name = "Trainings"
                category_id = "99"
                category_order = 0
                display_in_app = 0
            else:
                if not ben_obj.category and ben_obj.parent:
                    generalized, category_name = True, ben_obj.parent.name
                    category_id = str(ben_obj.parent.id)
                    category_order = ben_obj.parent.order
                else:
                    generalized, category_name = False, ben_obj.category.name
                    category_id = str(ben_obj.category.id)
                    category_order = ben_obj.category.order
        elif i.categories :
            category_name = i.categories.name
            category_id = i.categories.id
            category_order = i.categories.order
        else:
            category_name = "Activity"
            category_id = 0
            category_order = 0
        status = 1

        beneficiary_ids, beneficiary_type = all_beneficiary_ids.get(i.id), all_beneficiary_type.get(i.id)

        facility_ids, facility_type = "",""
        
        # if i.survey_type == 1:
        #     labels = all_labels.get(i.id)
        #     order_levels = all_order_levels.get(i.id)

        summary_qid = ','.join(','.join(map(str, item[2])) for item in filter_questions if item[1] == '1' and item[0] == i.id)
        search_filter = ','.join(','.join(map(str, item[2])) for item in filter_questions if item[1] == '3' and item[0] == i.id)
        if not summary_qid:
            survey_questions = load_data_to_cache_survey_based_questions()
            questions = survey_questions.get(str(i.id),{})
            summary_qids  = [x['id'] for x in questions if x['qtype'] in ['T', 'R', 'S', 'C']]
            summary_qid = ','.join(map(str, summary_qids[:3]))
        if int(i.periodicity) != 0:
            piriodicity = i.get_periodicity_display()
        else:
            piriodicity = ""
        get_survey_location = 2#all_survey_location.get(i.id)
        if (get_survey_location and get_survey_location >= user_level) or (i.survey_type == 0) :
            unique_questions = ""
            
            survey_json = []
            # survey_json.append({"b_type":i.location_beneficiary_id})

            child_survey = None
            version_updates.append({'vn': "1.0",
                                    'id': i.id,
                                    'summary_qid': summary_qid,
                                    'order_levels': order_levels,
                                    'beneficiary_ids': beneficiary_ids,
                                    'labels': labels,
                                    'parent_id': '',
                                    'beneficiary_type': beneficiary_type,
                                    'piriodicity': '1',\
                                    'piriodicity_flag': piriodicity,\
                                    'pLimit': plimit,\
                                    'pFeature': 3,
                                    'rule_engine': [],
                                    'reasonDisagree': 3,
                                    'survey_id': i.id,
                                    'survey_name': i.name,
                                    "survey_type": i.survey_type,
                                    "category_name": category_name,
                                    "category_id": category_id,
                                    "category_order": category_id,
                                    "modified_on": i.modified.strftime('%Y-%m-%d '
                                                                       '%H:%M:%S.%f'),
                                    "created_on": i.created.strftime('%Y-%m-%d '
                                                                     '%H:%M:%S.%f'),
                                    "active": i.active, "order": i.survey_order,
                                    "additional_days": '',
                                    "parents": "",
                                    'location_level': '',
                                    'display_name': display_name,
                                    'parent_link': [] ,
                                    'linkages': [],#i.get_beneficiary_linkages(),
                                    "constraints": unique_questions,
                                    "activity_description": description,
                                    "rule_engine": [],
                                    "rule_engine_or": [],
                                    "activity_rule_set": [],
                                    "category_rule_set": [],
                                    "display_in_app": display_in_app,
                                    "display_in_training": display_in_training,
                                    "is_training_survey": 0,
                                    "facility_ids": facility_ids,
                                    "facility_type": facility_type,
                                    "child_datacollection_ids": ','.join(map(str, child_survey)) if child_survey else '',
                                    "survey_categories": [{'id': i.categories.id, 'name': i.categories.name}] if i.categories else [],
                                    "search_filter":search_filter,
                                    "survey_json":survey_json ,
                                    "add": status,
                                    "is_activist_group": 1 if i.survey_module == 2 else 0,
                                    "activity_expenses":i.extra_config.get('activity_expenses',True) if i.extra_config else True,
                                    "expenses_questions": i.extra_config.get('expenses_questions',[]) if i.extra_config else [],
                                    "form_type": 1 if i.data_entry_level_id == 4 else 0,
                                    "role_type": i.extra_config.get('role_type', []),
                                    })
    return version_updates


@csrf_exempt
def surveylist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        status, message = 2, 'Survey list sent successfully'
        # state = StateSerializer(State.objects.filter(active=2),many=True).data
        proj_levellist = list(ProjectLevels.objects.filter(
            active=2).values_list('name', flat=True).order_by('name'))
        proj_levels = ",".join(proj_levellist)
        res = {'status': status,
               "message": "survey list sent successfully",
               "application_levels": str(proj_levels),
               'surveyDetails': get_latest_survey_versions(user_id),
               'survey_active_key': '',
               "display_as_code": 0,
                # "states":state,
               }
        return JsonResponse(res)

def get_all_survey_location(survey_list):
    all_location_level,location_level = {},None
    boundary_level_dict = {str(obj.id):obj for obj in BoundaryLevel}
    for sur in survey_list:
        for i in sur.config:
            for key in i.keys():
                indexvalue = key.split('_')[-1]
                if i[key] == "BoundaryLevel":
                    location_level  = boundary_level_dict.get(i.get('object_id_'+indexvalue))
                    if not location_level:
                        location_level = next((obj for obj_id, obj in boundary_level_dict.items() if str(obj.code) == i.get('object_id_'+indexvalue)), None)
        all_location_level[sur.id] = location_level   

    return all_location_level

def user_survey_level_labels_v3(survey_list, user_level):
    all_order_levels, all_labels = {}, {}
    boundary_level_dict = dict(BoundaryLevel.objects.filter(active=2).values_list('id','code'))
    boundary_level_name_dict = dict(BoundaryLevel.objects.filter(active=2).values_list('code','name'))
    order_levels, labels = get_orders_levels(user_level)


    for survey in survey_list:
        for i in survey.config:
            for key in i.keys():
                indexvalue = key.split('_')[-1]
                if i[key] == "BeneficiaryType":
                    # beneficiaryobj = BeneficiaryType.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
                    # beneficiary_type = str(beneficiary_types.get(int(i.get('object_id_' + indexvalue)),''))
                    # beneficiary_type = str(beneficiaryobj.name)
                    # beneficiary_ids = int(beneficiaryobj.get_survey().id)
                    order_levels, labels = get_orders_levels(user_level)
                elif i[key] == 'BoundaryLevel':
                    # boundaryobj = BoundaryLevel.objects.get_or_none(
                        # id=int(i.get('object_id_'+indexvalue)))
                    boundaryobj = boundary_level_dict.get(int(i.get('object_id_'+indexvalue)))
                    if boundaryobj and boundaryobj < user_level:
                        order_levels = ','.join(['level'+str(code) for k,code in boundary_level_dict.items() if code <= user_level])
                        labels = ','.join([name for code,name in boundary_level_name_dict.items() if code <= user_level])
                    elif boundaryobj:
                        # boundary_level_gte = BoundaryLevel.objects.filter(active=2, code__lte=boundaryobj, code__gte=user_level).order_by('code')
                        order_levels = ['level'+str(code) for k,code in boundary_level_dict.items() if code <= boundaryobj and code >= user_level]
                        # order_levels = ','.join(['level'+str(level.code) for level in boundary_level_gte])
                        labels = ','.join([name for code,name in boundary_level_name_dict.items() if code <= boundaryobj and code >= user_level])
        all_order_levels[survey.id] = order_levels
        all_labels[survey.id] = labels
    return all_order_levels, all_labels



def get_beneficiary_location_details_v3(user_level,survey_list):
    all_beneficiary_type,all_beneficiary_ids = {},{}
    # boundary_level_dict = {str(obj.id):obj for obj in BoundaryLevel.objects.filter(active=2)}
    boundary_type_dict = {obj.id:obj for obj in BeneficiaryType.objects.filter(active=2)}
    beneficiary_based_survey_dict = dict(Survey.objects.filter(active=2,survey_type=0, content_type_id=26).values_list('object_id','id'))
    for survey in survey_list:
        beneficiary_type,beneficiary_ids = '',''
        benf_type_list,benf_id_list =[],[]
        if survey.survey_type == 0:
            # beneficiaryobj = BeneficiaryType.objects.get_or_none(id = survey.object_id)
            beneficiaryobj = boundary_type_dict.get(survey.object_id)
            # beneficiary_ids = beneficiaryobj.get_survey().id
            beneficiary_ids = beneficiary_based_survey_dict.get(beneficiaryobj.id,"")
            beneficiary_type = beneficiaryobj.name
            # if survey.extra_config.get('user_level'):
                # boundary_level = cache.get(settings.INSTANCE_CACHE_PREFIX + 'get_boundary_level')
                # if not boundary_level:
                #     boundary_level = list(BoundaryLevel.objects.filter(active=2).order_by('code').values_list('id','code','name'))
                #     cache_set_with_namespace('RESPONSE_SURVEY_V3', 'get_boundary_level', boundary_level,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
                # boundary_level = BoundaryLevel.objects.filter(active=2,code__in=survey.extra_config.get('user_level')).order_by('code')
                # order_levels = ','.join(['level'+str(level[1]) for level in boundary_level if level[1] in survey.extra_config.get('user_level')])
                # labels = ','.join([level[2] for level in boundary_level if level[1] in survey.extra_config.get('user_level')])
            # else:
            #     order_levels , labels = get_orders_levels(user_level)
        else:
            for i in survey.config:
                for key in i.keys():
                    indexvalue = key.split('_')[-1]
                    if i[key] == "BeneficiaryType":
                        beneficiaryobj = boundary_type_dict.get(int(i.get('object_id_' + indexvalue)))
                        # beneficiaryobj = BeneficiaryType.objects.get_or_none(id=int(i.get('object_id_' + indexvalue)))
                        beneficiary_type = str(beneficiaryobj.name)
                        # beneficiary_ids = int(beneficiaryobj.get_survey().id)
                        beneficiary_ids = beneficiary_based_survey_dict.get(beneficiaryobj.id,"")
                        benf_id_list.append(beneficiary_ids)
                        benf_type_list.append(beneficiary_type)
                        # order_levels , labels = get_orders_levels(user_level)
                        
                    # elif i[key] == 'BoundaryLevel':
                    #     boundaryobj  = boundary_level_dict.get(i.get('object_id_'+indexvalue))
                    #     #BoundaryLevel.objects.get_or_none(id = int(i.get('object_id_'+indexvalue)))
                    #     if boundaryobj:
                    #         order_levels ,labels = get_boundary_levels_orders(boundaryobj,user_level)
            
        
        beneficiary_ids =  benf_id_list[0] if benf_id_list else beneficiary_ids
        beneficiary_type = benf_type_list[0] if benf_type_list else beneficiary_type
        # all_order_levels[survey.id] = order_levels
        # all_labels[survey.id] = labels
        all_beneficiary_type[survey.id] = beneficiary_type
        all_beneficiary_ids[survey.id] = beneficiary_ids
    return all_beneficiary_ids,all_beneficiary_type


@csrf_exempt
def get_language_app_label(request):
    status,message,res,responses = 0,"Data sent successfully",{},{}
    if request.method == 'POST':
        labeltrans_modified = request.POST.get('serverdatetime') # last modified date for label language translation
        # app label translation
        if labeltrans_modified: 
            labeltrans_queryset = LabelLanguageTranslation.objects.filter(modified__gt=labeltrans_modified).order_by('modified', 'id')
        else:
            labeltrans_queryset = LabelLanguageTranslation.objects.filter().order_by('modified','id')
        labeltrans_queryset = labeltrans_queryset[:100]
        responses = LabelLanguageTranslationSerializer(labeltrans_queryset, many=True).data
        status = 2
        if not labeltrans_queryset:
            message = "Data already sent"
    res = {'status':status,'message': message, 'translation': responses}
    return JsonResponse(res)

@csrf_exempt
def languagequestionlist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")
        flag = ""
        lang_questions = []
        updatedtime = request.POST.get("updatedtime")
        lang_quest = LanguageTranslationText.objects.filter(content_type=ContentType.objects.get_for_model(Question))
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_quest = lang_quest.filter(modified__gt=updated)
            flag = False
        lang_quest = lang_quest.filter().order_by('modified')[:100]
        for lq in lang_quest:
            if (lq.content_object and not lq.content_object.parent and lq.content_object.is_grid == False) or (lq.content_object and lq.content_object.parent and lq.content_object.is_grid == True):
                lang_questions.append({'id': int(lq.id),
                   'question_pid': int(lq.content_object.id),
                   'question_text': lq.text,
                   'language_id': int(lq.language.code),
                   'updated_time': datetime.strftime(lq.modified, '%Y-%m-%d %H:%M:%S.%f'),
                   'extra_column1': "",
                   'instruction': "",
                   'help_text': "",
                   'extra_column2': 0, })
        if lang_questions:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageQuestion": lang_questions, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No questions of different language has been tagged to this user", }
        return JsonResponse(res)


@csrf_exempt
def languagechoice(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")

        flag = ""
        l_ch = []
        updatedtime = request.POST.get("updatedtime")
        lang_ch = LanguageTranslationText.objects.filter(content_type=ContentType.objects.get_for_model(Choice))
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_ch = lang_ch.filter(modified__gt=updated)
            flag = False
        lang_ch = lang_ch.filter().order_by('modified')[:100]
        for ch in lang_ch:
            if ch.content_object:
                l_ch.append({"id": ch.id,
                             "option_pid": ch.content_object.id,
                             "question_pid": ch.content_object.question.id,
                             "language_id": int(ch.language.code),
                             "option_text": ch.text,
                             "validation": "",
                             "updated_time": datetime.strftime(ch.modified, '%Y-%m-%d %H:%M:%S.%f'),
                             "extra_column1": "",
                             'extra_column2': 0, })
        if l_ch:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageOptions": l_ch, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No choices of different language has been tagged to this user", }
        return JsonResponse(res)

@csrf_exempt
def assessmentlist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")

        questions = []
        flag = ""
        metrics_quest = []
        updatedtime = request.POST.get("updatedtime")
        metrics = Question.objects.filter(is_grid=False)
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            metrics = metrics.filter(modified__gt=updated)
            flag = False
        metrics = metrics.filter().exclude(parent=None).order_by('modified')[:100]
        for met in metrics:
#            if met.parent != None:
            metrics_quest.append({'id': int(met.id),
                                  'assessment': met.text,
                                  'question_pid': met.parent.id if met.parent else 0,
                                  'active': met.active,
                                  'mandatory': int(met.mandatory),
                                  'group_validation': met.get_question_validation() if met.get_question_validation() else "",
                                  'survey_id': int(met.block.survey.id),
                                  'language_id': 1,
                                  'updated_time': datetime.strftime(met.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                  'extra_column1': "",
                                  'extra_column2': 0,
                                  'qtype': met.qtype if met.qtype else "",
                                  'question_json': met.api_json,
                                  'code_display': str(met.code_display) if met.code_display  else '0', 
                                  'question_code': int(met.code),})
        if metrics_quest:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "Assessment": metrics_quest, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No grid questions tagged for this user", }
        return JsonResponse(res)    



@csrf_exempt
def languageassessmentlist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        count = request.POST.get("count")
        flag = ""
        lang_questions = []
        updatedtime = request.POST.get("updatedtime")
        lang_quest = LanguageTranslationText.objects.filter(content_type=ContentType.objects.get_for_model(Question))
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_quest = lang_quest.filter(modified__gt=updated)
            flag = False
        lang_quest = lang_quest.filter().order_by('modified')[:100]
        for lq in lang_quest:
            if lq.content_object and lq.content_object.parent and lq.content_object.is_grid == False:
                lang_questions.append({'id': int(lq.id),
                   'assessment_pid': int(lq.content_object.id),
                   'assessment': lq.text,
                   'language_id': int(lq.language.code),
                   'updated_time': datetime.strftime(lq.modified, '%Y-%m-%d %H:%M:%S.%f'),
                   'extra_column1': "",
                   'instruction': "",
                   'help_text': "",
                   'extra_column2': 0, })
        if lang_questions:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageAssessment": lang_questions, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No questions of different language has been tagged to this user", }
        return JsonResponse(res)

def get_res_dict(k,modified_date,user_id,usm,query,res_dict):
    if k == "MetricsQuestionConfiguration":
        result = Question.objects.filter(
            block__survey__id__in=usm, modified__gt=modified_date, is_grid=False)
    elif k == "MetricsQuestionTranslation":
        result = QuestionLanguageTranslation.objects.filter(
            question__block__survey__id__in=usm, modified__gt=modified_date, question__is_grid=True)
    elif k == "BlockLanguageTranslation":
        result = Block.objects.filter(survey__id__in=usm, modified__gt=modified_date)
    elif k == "ChoiceLanguageTranslation":
        result = Choice.objects.filter(question__block__survey__id__in=usm, modified__gt=modified_date)
    elif k == "QuestionLanguageTranslation":
        result = Question.objects.filter(
            block__survey__id__in=usm, modified__gt=modified_date)
    else:
        q = {query.get(k): usm, 'modified__gt': modified_date}
        result = apps.get_model('survey', k).objects.filter(**q)
    if result.count() > 0:
        res_dict[k] = True
    else:
        res_dict[k] = False
    return res_dict


@csrf_exempt
def updatedtables(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
#        usm = list(set(DetailedUserSurveyMap.objects.filter(
#            user__user__id=int(user_id)).values_list('survey__id', flat=True)))
        usm = Survey.objects.filter(active=2).values_list('id', flat=True)
        query = {
            "Block": "survey__id__in",
            "BlockLanguageTranslation": "block__survey__id__in",
            "Question": "block__survey__id__in",
            "QuestionLanguageTranslation": "question__block__survey__id__in",
            "Choice": "question__block__survey__id__in",
            "SkipMandatory": "question__block__survey__id__in",
            "ChoiceLanguageTranslation": "choice__question__block__survey__id__in",
        }
        res_dict = {}
        updated_dict = request.POST.get('UpdatedDateTime')
        updated_dict = literal_eval(updated_dict)

        updated_dict["BlockLanguageTranslation"] = updated_dict.pop(
            "LanguageBlock")
        print(updated_dict)        
        updated_dict["QuestionLanguageTranslation"] = updated_dict.pop(
            "LanguageQuestion")
        updated_dict["MetricsQuestionConfiguration"] = updated_dict.pop(
            "Assessment")
        updated_dict["MetricsQuestionTranslation"] = updated_dict.pop(
            "LanguageAssessment")
        updated_dict["Choice"] = updated_dict.pop("Options")
        updated_dict["ChoiceLanguageTranslation"] = updated_dict.pop(
            "LanguageOptions")
        updated_dict.pop("SkipRules")
        updated_dict.pop("LanguageLabels")
#        updated_dict.pop("MetricsQuestionConfiguration")
        updated_dict.pop("MetricsQuestionTranslation")
        for k, v in updated_dict.items():
            if v != "":
                modified_date = convert_string_to_date(str(v))
                get_res_dict(k,modified_date,user_id,usm,query,res_dict)
            else:
                res_dict[k] = True
            res_dict["SkipRules"] = False
            res_dict["LanguageLabels"] = False
            res_dict["MetricsQuestionTranslation"] = True
        res_dict["LanguageBlock"] = res_dict.pop("BlockLanguageTranslation")
        res_dict["LanguageQuestion"] = res_dict.pop(
            "QuestionLanguageTranslation")
        res_dict["Assessment"] = res_dict.pop("MetricsQuestionConfiguration")
        res_dict["LanguageAssessment"] = res_dict.pop(
            "MetricsQuestionTranslation")
        res_dict["Options"] = True if res_dict.get("Choice") else False
        res_dict["LanguageOptions"] = res_dict.pop("ChoiceLanguageTranslation")
        # userprofile_obj = UserRoles.objects.get(user__id=user_id)
        # version_update = VersionUpdate.objects.filter().latest('id')
        # updated_link = user_setup().get('updated_link',"") 
        updateapk = {"forceUpdate": "",
                     "appVersion": 0,
                     "updateMessage": "New update available, download from playstore",
                     "link":""}
        res = {'status': 2,
               'message': 'updated successfully',
               'updatedTables': res_dict}
        res.update({'updateAPK': updateapk,
                    'activeStatus': 2, 'forceLogout': 0, })
        res.update({'state_id':''})
    return JsonResponse(res, safe=False)



@csrf_exempt
def languagelist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uid")
        updatedtime = request.POST.get("updatedtime")
        usl = []
        flag=""
        #user_state = UserRoles.objects.get(user_id=int(user_id)).partner.state
        user_lang = Language.objects.filter(active=2)
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            user_lang = user_lang.filter(modified__gt=updated)
            flag = False
        for ul in user_lang:
            usl.append({"id": int(ul.id),
                        "language_code": int(ul.code),
                        "language_name": ul.name,
                        "active": ul.active,
                        "updated_date": datetime.strftime(ul.modified, '%Y-%m-%d %H:%M:%S.%f')})
        if usl:
            res = { 'status':2,\
                    'message':"Success",\
                    "regional_language": usl,}
        elif flag == False:
            res = { "status":2, \
                    "message":"Data already sent",}
        else:
            res= { "status":0, \
                    "message":"No languages has been tagged to this user",}
        return JsonResponse(res)        

def get_user_based_roles_locations(user):
    userrole = UserRoles.objects.get(user=user)
    locations = map(str,list(itertools.chain(OrganizationLocation.objects.filter(user=userrole).exclude(location=None).values_list('location__id',flat=True))))
    boundaries = Boundary.objects.filter(id__in=locations)
    user_roles = list(chain(userrole.role_type.all().values_list('id',flat=True)))
    return user_roles,locations

def groups_roles_locations_based_responses(survey_list,user):
    responses=[]
    input_parameters_1={}
    user_roles,locations = get_user_based_roles_locations(user)
    level = get_user_level(user)
    user_groups = get_user_location_group(locations)
    for survey in survey_list:
#        level = user_setup().get('least_location_level_config')
        if survey.is_beneficiary_based_child() == False:
            address_question = survey.questions().filter(api_json__is_address=2)
        else:
            address_question = survey.get_parent_beneficiary_address()
        role_question = survey.questions().get(api_json__is_role=2)
#        input_parameters = {'response__address__K1__' + str(address_question.id) + '__' + str(level)+'__icontains': locations,'response__K'+str(role_question.id)+'__icontains':user_roles}
        filters = Q()
        for i in user_roles:
            input_parameters_1 = {'response__K'+str(role_question.id)+'__icontains': i}
            filters |= Q(**{input_parameters_1.keys()[0]:input_parameters_1[input_parameters_1.keys()[0]]})
        json_response = JsonAnswer.objects.filter(filters,survey=survey)
        filters = Q()
        input_parameters_1 = {}
        if address_question:
            for address in address_question:
                for j in locations:
                    input_parameters_1 = ({'response__K'+str(address.id)+'__icontains': j})
                    #input_parameters_1=({'response__address__K1__K' + str(address.id) + '__K' + str(level)+'__icontains': j})
                    filters |= Q(**{input_parameters_1.keys()[0]:input_parameters_1[input_parameters_1.keys()[0]]})
        json_response = json_response.filter(filters)
        group_questions = survey.questions().filter(api_json__is_group=2)
        flag1 =False
        filters = Q()
        input_parameters_1 = {}
        if group_questions:
            flag1=True
            for grp_ques in group_questions:
                for i in user_groups:
                    input_parameters_1 = ({'response__K'+str(grp_ques.id)+'__icontains': i})
                    filters |= Q(**{input_parameters_1.keys()[0]:input_parameters_1[input_parameters_1.keys()[0]]})
        json_response = json_response.filter(filters)
        question_response=survey.questions().filter(api_json__is_response=2)
        flag2 = False
        input_parameters_1 = {}
        filters = Q()
        if question_response:
            flag2=True
            for res_ques in question_response:
                res_survey_id=res_ques.api_json.get('is_form')
                input_parameters_1 = {'response__K'+str(res_ques.id)+'=':res_survey_id}
                filters |= Q(**{input_parameters_1.keys()[0]:input_parameters_1[input_parameters_1.keys()[0]]})
        json_response = json_response.filter(filters)
        role_que = None
#        for item in input_parameters:
#            if item == 'response__K'+str(role_question.id)+'__icontains':
#                filters = Q(**{item:input_parameters[item]})
#        j = JsonAnswer.objects.filter(filters,survey=survey)
        responses.extend(json_response.values_list('id', flat=True))
    return responses

@csrf_exempt
def program_responses_list(request):
    if request.method == 'POST':
        # user_id = request.POST.get("userid")
        # user = User.objects.get(id=user_id)
        # updatedtime = request.POST.get("serverdatetime")
        # partner_obj = UserPartnerMapping.objects.get(user_id=int(user_id)).partner
        # survey_list=Survey.objects.filter(active=2,survey_module=1)
        # # survey_module = 1 for programs responses in swayam instance
        # # user_roles,locations = get_user_based_roles_locations(user)
        # # if not 'TEAM LEAD' in user_roles:
        # responses = groups_roles_locations_based_responses(survey_list,user)
        # responses_ids = list(set(responses))
        # user_list = UserPartnerMapping.objects.filter(partner=partner_obj).values_list('user',flat=True)
        # flag = ""
        # ben_uuid = ""
        # fac_uuid = ""
        # responses = JsonAnswer.objects.filter(active=2, id__in=responses_ids)
        # if updatedtime:
        #     updated = convert_string_to_date(updatedtime)
        #     responses = responses.filter(modified__gt=updated)
        #     flag = False
        # responses = responses.filter().order_by('modified')[:100]
        # res_list = get_common_responses_details(responses,partner_obj,user_id)
        # else:
        #     res_list = []
        res_list,flag = [],True
        if res_list:
            res = {'status': 2,
                   'message': "Success",
                   "ResponsesData": res_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No responses for this user", }
        return JsonResponse(res)
    
class MasterlookupDetails(g.CreateAPIView):
    
    def post(self, request):
        """API to list all MasterLookUp."""
        data=[] 
        try:
            if request.data.get('uId') and User.objects.filter(id = int(request.data.get('uId'))).exists():
                modified_date = request.data.get('serverdatetime')
                masterlookup = MasterLookUp.objects.all()
                if modified_date:
                    modified_date = convert_string_to_date(modified_date)
                    masterlookup = masterlookup.filter(modified__gt=modified_date)
                masterlookup = masterlookup.order_by('modified')[:100]
                data = [{'id': i.id,
                        'name': i.name,
                        'code': str(i.code),
                        'order':float(i.order),
                        'parent_id': i.parent.id if i.parent else 0,
                        'active': i.active,
                        'modified': datetime.strftime(i.modified, '%Y-%m-%d %H:%M:%S.%f'),
                        'locations':'',
                        } 
                        for i in masterlookup ]
                response = {'status':1, 'message':"masterlookup success", 'data':data}
            else:
                response = {'message': "user does not exist", 'status': 0, 'data':data}
        except Exception as e:
            response = {'message': e.args[0], 'status': 0, 'data':data}
        return Response(response)


def file_respone_details(res):
    import mimetypes
    file_data = ResponseFiles.objects.filter(active=2,content_type = ContentType.objects.get_for_model(res),object_id = res.id)
    file_data_list = []
    approved_status=''
    try:
        for fl_obj in file_data:
            '''
                * Below if condition is to send approve status of each and every file of response
                * Technically using for Content from cluster for KHPT/Sphoorthi
            '''
            inline_index = ''
            if res.survey.extra_config.get('cluster_activity') == 2:
                approved_status = 1 if fl_obj.approve else 0
            if fl_obj.response_image:
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
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(error_stack)
    return file_data_list

def get_common_responses_details(responses,partner_obj,user_id , user_roles=None):
    res_list = []
    flag = ""
    ben_uuid = ""
    fac_uuid = ""
    for res in responses:
        address_dict = {}
        if res.response.get('address') and res.survey.questions().filter(qtype='AW').exists():
            qid = res.survey.questions().filter(qtype='AW')[0].id
            address_dict = res.response.get('address').get('1').get(str(qid))
        if (res.survey.survey_type == 0 and res.get_beneficiary_object() and res.get_beneficiary_object().partner == partner_obj) or (res.user and str(res.user.id) == str(user_id)) or user_setup().get('share-approve-based-response') == 2:
            if not type(res.cluster) == list:
                cluster_beneficiary = res.cluster.get('BeneficiaryResponse', '') if res.cluster else ''
            else:
                cluster_beneficiary = ''
            grid_inline_questions = map(int,res.survey.questions().filter(qtype__in=['GD', 'In']).values_list('id',flat=True))
            if res.survey.survey_type == 0:
                cluster_id = res.get_beneficiary_object().get_beneficiary_address()
                cluster_name = Boundary.objects.get_or_none(id=cluster_id)
            else:
                try:
                    cluster_id = res.get_response_location()
                    cluster_name = Boundary.objects.get_or_none(id=cluster_id) if cluster_id else ''
                except:
                    cluster_name =''
            if res.cluster.get('Training'):
                ben_obj = BeneficiaryResponse.objects.get_or_none(creation_key=res.cluster.get('Training'))
                training_uuid = JsonAnswer.objects.get_or_none(id=ben_obj.json_answer_id).creation_key if ben_obj else ''
            else:
                training_uuid =''
#            if res.survey.survey_module == 2:
#                # this is to specify if the user logged in is tagged with the survivor activits groups or not 
#                # to know who is the leading the groups
#                active = 2 if res.lead_user and str(res.lead_user.id) == str(user_id) else 0
#            else: 
            try:
                active = res.cluster['active']
            except:
                if user_roles and 'lead-caseworker' in RoleTypes.objects.filter(id__in=user_roles).values_list('slug',flat=True):
                    active = res.active if res.lead_user_id ==int (user_id) or not res.lead_user_id else 0
                else:
                    active = res.active
            files_data = file_respone_details(res)
            '''
            #1 did only in KHPT for sending approved/pending status of peer girls response
            approved_status = ''
            if res.survey.extra_config.get('beneficiary_as_user'):
                approved_status = 0
                role_obj = UserRoles.objects.get_or_none(uuid=res.creation_key)
                if role_obj and role_obj.user.is_active:
                    approved_status = 1
            #1
            
            #2 KHPT special programs ('shared survey')
            sr_st = 0
            if res.survey.extra_config.get('shared_activity'):
                sp_prog = SharedResponseUserRelation.objects.get_or_none(response_id=res.id)
                if sp_prog:
                    if sp_prog.status == 3:
                        approved_status = 0
                    else:
                        approved_status = sp_prog.status
                    sr_st = sp_prog.share_status
                else:
                    sr_st,approved_status = 0,''
            '''
            # 2
            if res.survey.extra_config.get('share_response') == 2:
                approved_status = 0
                if ResponseFiles.objects.filter(content_type=ContentType.objects.get_for_model(res),object_id=res.id).exists():
                    try:
                        rf = ResponseFiles.objects.get_or_none(content_type=ContentType.objects.get_for_model(res),object_id=res.id)
                    except:
                        rf = None
                    if rf:
                        approved_status = 1 if rf.approve == True else 0
            res_list.append({"response_id": res.id,
                            "app_answer_on": datetime.strftime(
                                 res.app_answer_on, '%Y-%m-%d %H:%M:%S') if res.app_answer_on else '',
                             "bene_uuid": res.creation_key,
                             "l_id": str(res.language.id) if res.language else '1',
                             "survey_id": int(res.survey.id),
                             "cluster_id": int(cluster_id) if cluster_id != None and cluster_id != '' and cluster_id != 'None' else 0,
                             "cluster_name": cluster_name.name if cluster_name else '',
                             "ben_parent_uuid":res.get_beneficiary_object().creation_key if res.get_beneficiary_object() else '',
                             "response_dump":get_actual_response(res.response),
                             "collected_date": datetime.strftime(
                                 res.submission_date, '%Y-%m-%d'),
                             "active": active,
                             "server_date_time": datetime.strftime(
                                 res.modified, '%Y-%m-%d %H:%M:%S.%f'),
                             'location': address_dict,
                             'cluster_beneficiary': cluster_beneficiary,
                             'training_survey':res.training_survey.id if res.training_survey else 0,
                             'training_survey_id': str(res.beneficiary_type.get_survey().id) if res.beneficiary_type else "",
                             'training_uuid': training_uuid,
                             'grid_inline_questions': grid_inline_questions,
                             'facility_uuid':res.cluster.get('Facility',''),
                             'batch_uuid':res.cluster.get('Batch',''),
                             'task_uuid':res.cluster.get('Task',''),
                             'image_info': res.get_image_info(),
                             'user_id':res.user.id if res.user else '',
                             'child_reference_id':res.cluster.get('child_reference_id',''),
                             'files_info':files_data,
                             # 'approved_status':approved_status,
                             # 'sr_st':sr_st,
                             'project_id':res.cluster.get('project_id' , 0),
                             })
    return res_list

import itertools       
def user_based_group_responses():

#    """if 'lead-caseworker' in RoleTypes.objects.filter(id__in=user_roles).values_list('slug',flat=True):
#        #responses = list(itertools.chain(JsonAnswer.objects.filter(survey__id=survey_list.values_list('id',flat=True),lead_user=user).values_list('id',flat=True)))
#        responses = list(itertools.chain(JsonAnswer.objects.filter(survey__id=survey_list.values_list('id',flat=True)).values_list('id',flat=True)))
#    else:"""
    responses = list(itertools.chain(JsonAnswer.objects.filter().values_list('id',flat=True)))
    return responses
def get_survivors_linkages_responses():
    # if 'lead-caseworker' in RoleTypes.objects.filter(id__in=user_roles).values_list('slug',flat=True):
    try:
        # ben_ids = BeneficiaryResponse.objects.filter(json_answer_id__in=responses)
        # linkages = BeneficiaryLink.objects.filter(object_id__in=ben_ids,content_type=ContentType.objects.get_for_model(BeneficiaryResponse.objects.get_or_none(id=ben_ids[0].id))).values_list('object_id1',flat=True)
        linkage_responses = list(itertools.chain(JsonAnswer.objects.filter().values_list('id',flat=True)))
    except:
        linkage_responses=[]
    # else:
    #     linkage_responses=[]
    return linkage_responses

def lead_activites_responses(user,user_roles):
    activity_list=[]
    act_responses=[]
    # if not 'lead-caseworker' in RoleTypes.objects.filter(id__in=user_roles).values_list('slug',flat=True):
    surveys = Survey.objects.filter(survey_module)
    surveys = Survey.objects.filter(survey_module=2)
    for i in surveys:
        activities = list(itertools.chain(Survey.objects.filter(config__0__content_type_1='BeneficiaryType',config__0__object_id_1=str(i.object_id)).values_list('id',flat=True)))
        activity_list.extend(activities)
    act_responses = list(itertools.chain(JsonAnswer.objects.filter(survey__id__in=activity_list).values_list('id',flat=True)))
    return act_responses

@csrf_exempt
def avtivist_group_responses(request):
    if request.method == 'POST':
#         user_id = request.POST.get("userid")
#         user = User.objects.get(id=user_id)
# #        """#updatedtime = request.POST.get("serverdatetime")"""
#         partner_obj = UserPartnerMapping.objects.get(user_id=int(user_id)).partner
#         survey_list=Survey.objects.filter(active=2,survey_module=2)
# #        """# survey_module = 2 for survivor activits group in swayam instance"""
#         # user_roles,locations = get_user_based_roles_locations(user)
#         responses = user_based_group_responses()
#         linkage_responses = get_survivors_linkages_responses()
#         if linkage_responses:
#             responses.extend(linkage_responses)
#         # activity_responses = lead_activites_responses(user,user_roles)
#         # responses.extend(activity_responses)
#         user_list = UserRoles.objects.filter(partner=partner_obj).values_list('user',flat=True)
#         flag = ""
#         ben_uuid = ""
#         fac_uuid = ""
#         responses = JsonAnswer.objects.filter(active=2, id__in=responses)
# #        if updatedtime:
# #            updated = convert_string_to_date(updatedtime)
# #            responses = responses.filter(modified__gt=updated)
# #            flag = False
# #        responses = responses.filter().order_by('modified')[:100]
#         res_list = get_common_responses_details(responses,partner_obj,user_id, user_roles)
        res_list,flag = [],True
        if res_list:
            res = {'status': 2,
                   'message': "Success",
                   "ResponsesData": res_list, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No responses for this user", }
        return JsonResponse(res)
    
# class ProgramRetreiveLinkages(CreateAPIView):
#     serializer_class = LinkageListingSerializer
#     def post(cls, request, format=None):
#         response = {'status': "success", "message": "successfully done"}
#         serializer = LinkageListingSerializer(data=request.data)
#         if serializer.is_valid():
#             data_dict = {'content_type':ContentType.objects.get_for_model(BeneficiaryResponse),
#                 'content_type1':ContentType.objects.get_for_model(BeneficiaryResponse),
#                 'relation':None,
#                 'survey_relation':1
#                 }
#             linkage_list,flag = get_common_linkage_details(request,data_dict)
#             response.update({'linkages': linkage_list})
#         else:
#             return get_serializer_errors(serializer)
#         return Response(response)    
    

@csrf_exempt
def get_levels(request, level):
    try:
        n = 100
        # url_level = level

    #    userrole = UserRoles.objects.get(user__id=request.POST.get('uid'))
    #    orguser = OrganizationLocation.objects.filter(user__id=userrole.id)
        user = User.objects.get(id=request.POST.get('uid'))
        boundary_level = {1:State,2:District}
        tagged_locations = UserProjectMapping.objects.filter(user=user,active=2).select_related('project','project__district','project__district__state')
        # level_obj = BoundaryLevel.objects.get(code=int(url_level))
        # user_locations = user_projects_locations(user, level_obj)
        # tagged_locations = Boundary.objects.filter(id__in=user_locations)
        tagged_locations_all = tagged_locations
        modified_obj = request.POST.get("modified_date")
        if modified_obj:
            modified_date = convert_string_to_date(modified_obj)
            tagged_locations = tagged_locations.filter(modified__gt=modified_date)

        parent_locations = []
        tagged_locations = tagged_locations.order_by('modified')[:int(n)]

        for tl in tagged_locations:
            one_location_level = {}
            if level == 1:
                location = tl.project.district.state
            else:
                one_location_level['level1_id']=int(tl.project.district.state.id)
                location = tl.project.district
            
            one_location_level['level'+str(level)+'_id']=int(location.id)
            one_location_level['name']=re.sub(r'[^\x00-\x7F]+','',location.name).strip()
            one_location_level['active']=str(location.active)
            one_location_level['modified_date']=datetime.strftime(location.modified, '%Y-%m-%d %H:%M:%S.%f')
            try:
                rural = MasterLookUp.objects.get(id=location.object_id)
                one_location_level['location_type']=str(rural.name)
            except:
                one_location_level['location_type']=""
            parent_locations.append(one_location_level)
        if len(parent_locations) == int(n):
            flag = 2
        else:
            flag = 1
        if parent_locations:
            return JsonResponse({'status':2,'Level '+str(level):parent_locations,'flag':flag,'location_ids':list(tagged_locations_all.values_list('id',flat=True))
                        })
        else:
            return JsonResponse({"status":2, "message":"Data already sent",})
    except Exception as e:
        return JsonResponse({'status':0,'message':"Something went wrong","error":e.args[0]})



@csrf_exempt
def languageblocklist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        updatedtime = request.POST.get("updatedtime")
        count = request.POST.get("count")
        lang_blocks = []
        flag = ""
        lang_bl = Block.objects.filter().exclude(language_code={})
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            lang_bl = lang_bl.filter(modified__gt=updated)
            flag = False
        lang_bl = lang_bl.filter().order_by('modified')[:100]
        for lb in lang_bl:
            for lang,l_text in lb.language_code.items():
                lan_obj = Language.objects.get(id=int(lang))
                lang_blocks.append({'id': int(lb.id),
                                    'block_pid': int(lb.id),
                                    'block_name': l_text,
                                    'language_id': int(lan_obj.code),
                                    'updated_time': datetime.strftime(lb.modified, '%Y-%m-%d %H:%M:%S.%f'),
                                    'extra_column1': str(lan_obj.name),
                                    'extra_column2': 0, })
        if lang_blocks:
            res = {'status': 2,
                   'message': "Data sent successfully",
                   "LanguageBlock": lang_blocks, }
        elif flag == False:
            res = {"status": 2,
                   "message": "Data already sent", }
        else:
            res = {"status": 0,
                   "message": "No blocks of different language has been tagged to this user", }
        return JsonResponse(res)


@csrf_exempt
def feed_error_log(request):
    status, message = False, ''
    if request.method == 'POST':
        user_id = request.POST.get('uId')
        error_log = request.POST.get('ErrorLog')
        stoken = request.POST.get('sToken')
        user_obj = User.objects.get(id=int(user_id))
        if user_obj:
            f = logdata(error_log, user_obj, stoken)
            status = True
            message = "ErrorLog Data saved successfully"
    res = {'status': status, 'message': message}
    return JsonResponse(res)


def logdata(error_log, user_obj, stoken):
    from mfv_mis.settings import BASE_DIR
    from django.core.files.base import ContentFile, File
    import time
    unique_time = int(time.time())
    today_date = datetime.now()
    year = today_date.strftime("%Y")
    dt = today_date.strftime("%d")
    m = today_date.strftime("%m")
    hour = today_date.strftime("%H")
    minute = today_date.strftime("%M")
    new_file_path = '%s/media/logfiles/%s/%s/%s/' % (BASE_DIR,year,m,dt)
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)
    file_name = "ErrorLog" + "-" + str(user_obj.id) + "-" + str(unique_time) + "-" + year + "-" + m + "-" + dt + ".txt"
    # full_filename = os.path.join(BASE_DIR,new_file_path,file_name)
    full_filename = new_file_path+file_name
    logger.info("Date : " + dt + "-" + m + "-" + year + "\n")
    logger.info("Time : "+ hour + "hrs" + ":" + minute + "min" + "\n\n")
    logger.info("Error : "+error_log)
    with open(full_filename, 'w+', encoding='utf-8') as text_file:
        text_file.writelines("Date : " + dt + "-" + m + "-" + year + "\n")
        # text_file.write(bytes("Date : " + dt + "-" + m + "-" + year + "\n", encoding="raw_unicode_escape"))
        text_file.writelines("Time : "+ hour + "hrs" + ":" + minute + "min" + "\n\n")
        # text_file.write(bytes("Time : "+ hour + "hrs" + ":" + minute + "min" + "\n\n", encoding="raw_unicode_escape"))
        text_file.writelines("Error : "+error_log)
        # text_file.write(bytes("Error : "+error_log, encoding="raw_unicode_escape"))
        elog_obj = ErrorLog.objects.create(user=user_obj, stoken=stoken)
        # elog_obj.log_file = File(text_file)
        print(text_file)
        elog_obj.log_file.save(file_name, File(text_file))
        if os.path.exists(full_filename):
            os.remove(full_filename)
        elog_obj.save()
        text_file.close()
    return True