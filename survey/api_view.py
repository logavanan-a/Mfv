from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from survey.models import *
# from survey.custom_decorators import *
# from survey.monkey_patching import *
# from masterdata.models import *
# from beneficiary.models import *
import os
from datetime import datetime, timedelta
from django.db.models import Q
from django.apps import apps
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


@csrf_exempt
def surveylist(request):
    if request.method == 'POST':
        user_id = request.POST.get("uId")
        status, message = 2, 'Survey list sent successfully'
        state = StateSerializer(State.objects.filter(active=2),many=True).data
        proj_levellist = list(ProjectLevels.objects.filter(
            active=2).values_list('name', flat=True).order_by('name'))
        proj_levels = ",".join(proj_levellist)
        res = {'status': status,
               "message": "survey list sent successfully",
               "application_levels": str(proj_levels),
               'surveyDetails': get_latest_survey_versions(user_id),
               'survey_active_key': '',
               "display_as_code": user_setup().get("is_code_display") if user_setup().get("is_code_display") else 0,
                "states":state,
               }
        return JsonResponse(res)
    
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

