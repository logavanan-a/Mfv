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
import os
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
from ast import literal_eval
from django.db.models import Q,F
import sys, traceback
import  logging
from django.conf import settings
from collections import defaultdict
from application_master.models import BoundaryLevel


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
                                #    "validation":  quest.get_question_validation() if quest.get_question_validation() else "" ,
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
        choice = Choice.objects.all().select_related('question','question__block','question__block__survey').prefetch_related('boundary','skip_question')
        if updatedtime:
            updated = convert_string_to_date(updatedtime)
            choice = choice.filter(modified__gt=updated)
            flag = False
        choice = choice.filter().order_by('modified')[:100]
        for ch in choice:
            skip_quest = ""
            if ch.skip_question.all():
                val = [str(i) for i in sorted(ch.skip_question.ids())]
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
                            'locations': ','.join(map(str,ch.boundary.all().values_list('id',flat=True)))  if ch.boundary.all()  else "" ,
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
    all_order_levels, all_labels = user_survey_level_labels_v3(survey_list, user_level)

    all_order_levels, all_labels, all_beneficiary_ids, all_beneficiary_type = get_beneficiary_location_details_v3(user_level, survey_list)
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

        order_levels, labels, beneficiary_ids, beneficiary_type = all_order_levels.get(i.id), all_labels.get(i.id), all_beneficiary_ids.get(i.id), all_beneficiary_type.get(i.id)

        facility_ids, facility_type = "",""
        
        if i.survey_type == 1:
            labels = all_labels.get(i.id)
            order_levels = all_order_levels.get(i.id)

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
        if (get_survey_location and get_survey_location.code >= user_level) or (i.survey_type == 0) :
            unique_questions = ""
            
            survey_json = []
            survey_json.append({"b_type":i.location_beneficiary_id})

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
                                    'linkages': i.get_beneficiary_linkages(),
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
    order_levels, labels ="level1,level2","State,District" # get_orders_levels(user_level)


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
    all_order_levels, all_labels,all_beneficiary_type,all_beneficiary_ids = {},{},{},{}
    boundary_level_dict = {str(obj.id):obj for obj in BoundaryLevel.objects.filter(active=2)}
    boundary_type_dict = {obj.id:obj for obj in BeneficiaryType.objects.filter(active=2)}
    beneficiary_based_survey_dict = dict(Survey.objects.filter(active=2,survey_type=0, content_type_id=26).values_list('object_id','id'))
    for survey in survey_list:
        order_levels, labels,beneficiary_type,beneficiary_ids = '','','',''
        benf_type_list,benf_id_list =[],[]
        if survey.survey_type == 0:
            # beneficiaryobj = BeneficiaryType.objects.get_or_none(id = survey.object_id)
            beneficiaryobj = boundary_type_dict.get(survey.object_id)
            # beneficiary_ids = beneficiaryobj.get_survey().id
            beneficiary_ids = beneficiary_based_survey_dict.get(beneficiaryobj.id,"")
            beneficiary_type = beneficiaryobj.name
            if survey.extra_config.get('user_level'):
                boundary_level = cache.get(settings.INSTANCE_CACHE_PREFIX + 'get_boundary_level')
                if not boundary_level:
                    boundary_level = list(BoundaryLevel.objects.filter(active=2).order_by('code').values_list('id','code','name'))
                    cache_set_with_namespace('RESPONSE_SURVEY_V3', 'get_boundary_level', boundary_level,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
                # boundary_level = BoundaryLevel.objects.filter(active=2,code__in=survey.extra_config.get('user_level')).order_by('code')
                order_levels = ','.join(['level'+str(level[1]) for level in boundary_level if level[1] in survey.extra_config.get('user_level')])
                labels = ','.join([level[2] for level in boundary_level if level[1] in survey.extra_config.get('user_level')])
            else:
                order_levels , labels = get_orders_levels(user_level)
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
                        order_levels , labels = get_orders_levels(user_level)
                        
                    elif i[key] == 'BoundaryLevel':
                        boundaryobj  = boundary_level_dict.get(i.get('object_id_'+indexvalue))
                        #BoundaryLevel.objects.get_or_none(id = int(i.get('object_id_'+indexvalue)))
                        if boundaryobj:
                            order_levels ,labels = get_boundary_levels_orders(boundaryobj,user_level)
            
        
        beneficiary_ids =  benf_id_list[0] if benf_id_list else beneficiary_ids
        beneficiary_type = benf_type_list[0] if benf_type_list else beneficiary_type
        all_order_levels[survey.id] = order_levels
        all_labels[survey.id] = labels
        all_beneficiary_type[survey.id] = beneficiary_type
        all_beneficiary_ids[survey.id] = beneficiary_ids
    return all_order_levels,all_labels,all_beneficiary_ids,all_beneficiary_type


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
                                #   'group_validation': met.get_question_validation() if met.get_question_validation() else "",
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
                        'locations':i.get_masterdata_locations(),
                        } 
                        for i in masterlookup ]
                response = {'status':1, 'message':"masterlookup success", 'data':data}
            else:
                response = {'message': "user does not exist", 'status': 0, 'data':data}
        except Exception as e:
            response = {'message': e.args[0], 'status': 0, 'data':data}
        return Response(response)
        
@csrf_exempt
def new_responses_list_v3(request):
    # get user and based on userid get surveys mapped to user
    # get active survey id
    if request.method == 'POST':
        user_id = request.POST.get("userid")
        logger.info("##TIME-TRACKER (Start - " + user_id + "): " + str(datetime.now()))
        user_role = UserRoles.objects.get(user_id=user_id)
        ben_modified_date_str = request.POST.get("ben_modified_date")
        ben_modified_date = convert_string_to_date(ben_modified_date_str)
        hd_modified_date_str = request.POST.get("hd_modified_date")
        hd_modified_date = convert_string_to_date(hd_modified_date_str)
        hd_modified_date_str = convert_date_to_string(hd_modified_date)
        act_modified_date_str = request.POST.get("act_modified_date")
        act_modified_date = convert_string_to_date(act_modified_date_str)
        act_modified_date_str = convert_date_to_string(act_modified_date)
        # partner_obj = UserRoles.objects.get(user_id=int(user_id)).partner
        user_specific_responses = user_setup().get('user_location_responses', 0)
        loc_list = []

        # Add and call it from  setting.py
        # TODO: change to RESPONSES_V3 and add RESPONSES_V3 - batch_size in settings
        batch_count = settings.SYNC_SETTINGS['RESPONSES_V3']['BATCH_SIZE']
        t1 = datetime.now()
        if user_specific_responses == 2:
            loc_list_cache_key = "user_project_based_boundary__" + user_id
            loc_list = cache.get(settings.INSTANCE_CACHE_PREFIX + loc_list_cache_key)
            if not loc_list:
                user_boundary = list(user_role.get_poject_based_location())
                loc_list = [str(i) for i in user_boundary]
                cache_set_with_namespace('RESPONSE_SURVEY_V3', loc_list_cache_key, loc_list, 14400)
                logger.info("## TIME-TRACKER UserID-loc_list::" + str(user_id) + " : " + str(loc_list))
            if len(loc_list) > 0:
                boudnary_level_filter = user_role.organization_unit.organization_level_id
                query_set = {f"address_{boudnary_level_filter}__in": loc_list}
                beneficiaries_json = BeneficiaryResponse.objects.filter(**query_set).values_list('json_answer_id', flat=True)

                beneficiaries = JsonAnswer.objects.filter(id__in=beneficiaries_json).order_by('modified')
                if ben_modified_date:
                    beneficiaries = beneficiaries.filter(modified__gt=ben_modified_date)
                
                responses = beneficiaries[:batch_count]
                logger.info("#############-----------TIME-TRACKER (Beneficiaries-CommonResponse - Start): " + str(datetime.now()))
                res_list = common_responses_details_v3(responses, user_id,user_role)
                logger.info("#############-----------TIME-TRACKER (Beneficiaries-CommonResponse - End): " + str(datetime.now()))
                logger.info("#############----------TIME-TRACKER (Beneficiaries - ResponseCount): " + str(len(res_list)))
                
                # logger.info("#############TIME-TRACKER (Beneficiaries-End): " + str(datetime.now()))
                # if len(res_list) == 0:
                #     # # TODO : address fields to be updated for beneficiary table old records
                #     # logger.info("#############TIME-TRACKER (Beneficiaries(321)- Start): " + str(datetime.now()))
                #     household_details = JsonAnswer.objects.filter(
                #         survey_id=321, boundary_id__in=loc_list).order_by('modified')
                #     if hd_modified_date:
                #         household_details = household_details.filter(
                #             modified__gt=hd_modified_date)
                #     responses = household_details[:batch_count]
                #     # logger.info("#############-----------TIME-TRACKER (Beneficiaries(321)-CommonResponse - Start): " + str(datetime.now()))
                #     res_list = common_responses_details_v3(
                #         responses, user_id)
                #     # logger.info("#############-----------TIME-TRACKER (Beneficiaries(321)-CommonResponse - End): " + str(datetime.now()))
                #     logger.info(
                #         "#############----------TIME-TRACKER (Beneficiaries(321) - ResponseCount): " + str(len(res_list)))
                # logger.info("#############TIME-TRACKER (Beneficiaries(321)- End): " + str(datetime.now()))
                if len(res_list) == 0:
                    # logger.info("#############TIME-TRACKER (Activities-Start): " + str(datetime.now()))
                    cache_key = 'user_based_surveys' + '-' + user_id
                    lineitem_obj = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
                    if not lineitem_obj:
                        project_list = ProjectUserRelation.objects.filter(user__in=[user_role.id]).values_list('project', flat=True)
                        lineitem_obj = list(Lineitem.objects.filter(active=2, project__in=project_list).values_list('activity', flat=True))
                        location_based_survey = list(Survey.objects.filter(active=2,survey_type=1,data_entry_level_id=1).values_list('id',flat=True))
                        lineitem_obj += location_based_survey
                        cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, lineitem_obj, 14400)

                    cache_key = 'user_based_form_surveys'
                    user_based_survey = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key)
                    if not user_based_survey:
                        user_based_survey = list(Survey.objects.filter(active=2,survey_type=1,data_entry_level_id=4).values_list('id',flat=True))
                        cache_set_with_namespace('RESPONSE_SURVEY_V3', cache_key, user_based_survey, 14400)

                    # activities =  JsonAnswer.objects.filter(survey_id__in=lineitem_obj,boundary_id__in = loc_list,submission_date__date__gte=fy_date).order_by('modified')
                    if boudnary_level_filter != 5:
                        loc_list = Boundary.objects.filter(id__in=loc_list)
                        loc_list = get_higher_level_locations(loc_list, boudnary_level_filter, 5)

                    #current financial year start and end
                    financial_year = get_financial_years()
                    
                    project_location_query = Q(survey_id__in=lineitem_obj, boundary_id__in=loc_list)
                    userbased_query = Q(survey_id__in=user_based_survey,user_id=user_id)
                    activities = JsonAnswer.objects.filter(project_location_query | userbased_query,submission_date__date__range=[financial_year['current_financial_start'],financial_year['current_financial_end']]).order_by('modified')
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
        else:
            res = {"status": 0,
                   'batch_size': batch_count,
                   'current_record_count': 0,
                   "message": "Invalid User", }
        logger.info("##TIME-TRACKER (End (ResponseCount) - " + user_id +
                    " : " + str(len(res_list)) + "): " + str(datetime.now()))
        return JsonResponse(res)    

