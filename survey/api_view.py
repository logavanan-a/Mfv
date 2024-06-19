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
                                   'individual_qid': quest.reference_question_id or 0 ,
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