# -*- coding: utf-8 -*-
# form views
from django.views.generic import View, RedirectView
from django.shortcuts import render,HttpResponse,HttpResponseRedirect
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType
from dateutil.relativedelta import relativedelta
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from application_master.models import *
from survey.models import *
import sys, traceback
from django.http import JsonResponse

# from configuration_settings.user_views import get_pagination
# from partner.models import Partner
# # from userroles.serializers import user_setup # get_session_name
# from userroles.models import UserRoles,RoleTypes
# from masterdata.models import BoundaryLevel, Boundary, MasterLookUp
# from masterdata.serializers import BackendSearchSerializer
# from projectmanagement.models import Project, Lineitem
# from projectmanagement.views import get_activity_details
# from configuration_settings.decorators import validate_partner_user, validate_partner_user_for_baseline
import requests
from django.conf import settings
import json
import uuid
from django.contrib.auth.models import User
from datetime import datetime,timedelta
# from beneficiary.views import update_question_answers
from django.utils.encoding import smart_str
import csv
import urllib3
import logging
from django.db.models import Q
from django.db import connection
# from userroles.serializers import get_session_name
from cache_configuration.views import *
from django.db.models import Case, When
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from mfv_mis.settings import DATE_DISPLAY_FORMAT,MONTH_DISPLAY_FORMAT,INSTANCE_CACHE_PREFIX
# from transfer_module.forms import TransferRequestForm
from django.db import transaction

logger = logging.getLogger(__name__)


pg_size = settings.WEBPAGINATIONPAGECOUNT

def web_pagination(request,users):
    paginator = Paginator(users, pg_size) # Show no of object per page
    page = request.GET.get('page',1)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    return users

def multi_key_dict_get(d, k):
    for keys, v in d.items():
        if k in keys:
            return v
    return None

def get_result_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()

def getFromDict(dataDict, mapList):
    value = dataDict
    for key in mapList:
        value = value.get(key,'')
    return value

def indexer(id,width):
    # str(int(result[0][0][last_idx:])+1).zfill(width)
    number='%0*d' % (width, int(id or 0)+1)
    return str(number)

def cache_set_with_namespace(namespace, key, value,cache_time = None):
     namespace_key = "__NS__"+namespace+"__NS__"
     ns_list = cache.get(namespace_key)
     if not ns_list:
          ns_list = []
     if key not in  ns_list:
        ns_list.append(key)
     if cache_time:
        cache.set(namespace_key, ns_list,cache_time)
     else:
        cache.set(namespace_key, ns_list,86400)
     cache.set(key,value)


def load_data_to_cache_questions():
    #caching the questions based on the questions
    query = "SELECT jsonb_object_agg(id, question_info) FROM ( SELECT a.id, jsonb_build_object( 'qtype', a.qtype, 'text', a.text, 'training_config', a.training_config ) AS question_info FROM survey_question a GROUP BY a.id ) AS x"

    cache_key_questions = INSTANCE_CACHE_PREFIX+'question_meta'
    questions =  cache.get(cache_key_questions)
    if not questions:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            questions = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_questions,questions,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return questions

def load_data_to_cache_boundary_meta():
    #caching the boundary
    query = "SELECT jsonb_object_agg(id, bondary) FROM ( SELECT a.id, jsonb_build_object( 'name', a.name, 'parent',p.name ) AS bondary FROM application_master_boundary a LEFT JOIN application_master_boundary p on p.id = a.parent_id ) AS x"

    cache_key_boundary = INSTANCE_CACHE_PREFIX+'boundary_meta'
    boundaries =  cache.get(cache_key_boundary)
    if not boundaries:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            boundaries = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_boundary,boundaries,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return boundaries

def question_based_answers(survey_id,answer,questions):
    final_result = {}
    questions_dict = load_data_to_cache_questions()
    for question_id in questions:
        single_question = questions_dict.get(str(question_id))
        if single_question.get('qtype') != 'H':
            aw_or_ans = answer.get(str(question_id)) if single_question.get('qtype') != 'AW' else answer.get('address')
            ans = get_answer(aw_or_ans,single_question)
            final_result.update({single_question.get('text'):ans})
    return final_result


def load_data_to_cache_choice_meta():
    #caching the questions based on the questions
    query = "SELECT jsonb_object_agg(id, choice_info) FROM ( SELECT a.id, jsonb_build_object( 'name', a.text ) AS choice_info FROM survey_choice a ) AS x"

    cache_key_choice = INSTANCE_CACHE_PREFIX+'choice_meta'
    choices =  cache.get(cache_key_choice)
    if not choices:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            choices = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_choice,choices,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return choices


import re
from datetime import date
def get_answer(answer,question):
    if (answer in [None,'None','']) and question.get('qtype') != 'AW': 
        return '-'
    elif question.get('qtype') in ['C','S','SM']:
        if question.get('qtype') == 'SM':
            choices = load_data_to_cache_masterlookup_meta()
        else:
            choices = load_data_to_cache_choice_meta()
        selected_choice=choices.get(str(answer))
        # selected_choices = map(choice_dict.get, map(str, item_list))
        return selected_choice.get('name')
    elif question.get('qtype') == 'AW':
        boundaries = load_data_to_cache_boundary_meta()
        lower_lewel = list(answer.get('1').values())
        district =boundaries.get(lower_lewel[0].get('2'), {})
        return f'{district.get("parent")}({district.get("name")})'
    elif question.get('qtype') == 'AI':
        json_name = JsonAnswer.objects.get(creation_key=answer).response.get('235')
        return json_name
    elif question.get('qtype') == 'D':
        date_format = re.compile(r'\d{2}-\d{2}-\d{4}')
        age=None
        if not date_format.match(answer) and not question.get('training_config').get('month'):
            date_object = datetime.strptime(answer, '%Y-%m-%d')
            answer=date_object.strftime(DATE_DISPLAY_FORMAT)
        elif not question.get('training_config').get('month'):
            date_object = datetime.strptime(answer, '%d-%m-%Y')
            answer=date_object.strftime(DATE_DISPLAY_FORMAT)
        elif question.get('training_config').get('month'):
            date_object = datetime.strptime(answer, '%m-%Y')
            answer=date_object.strftime(MONTH_DISPLAY_FORMAT)
        if question.get('training_config').get('dob'):
            today = date.today()
            age=today.year - date_object.year - ((today.month, today.day) < (date_object.month, date_object.day))
            answer=answer+"("+str(age)+")"
        return answer
    return answer


def load_data_to_cache_masterlookup_meta():
    #caching the masterlookup
    query = "SELECT jsonb_object_agg(id, masterlookup) FROM ( SELECT a.id, jsonb_build_object( 'name', a.name ) AS masterlookup FROM masterdata_masterlookup a ) AS x"

    cache_key_choice = INSTANCE_CACHE_PREFIX+'masterlookup_meta'
    master_lookup =  cache.get(cache_key_choice)
    if not master_lookup:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            master_lookup = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_choice,master_lookup,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return master_lookup

def question_based_answers(survey_id,answer,questions):
    print(answer,questions,'answer,questions')
    final_result = {}
    questions_dict = load_data_to_cache_questions()
    for question_id in questions:
        single_question = questions_dict.get(str(question_id))
        if single_question.get('qtype') != 'H':
            aw_or_ans = answer.get(str(question_id)) if single_question.get('qtype') != 'AW' else answer.get('address')
            ans = get_answer(aw_or_ans,single_question)
            final_result.update({single_question.get('text'):ans})
    return final_result


    

def load_data_to_cache():
    #Survey listing page choices 
    cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices'
    survey_heading_choices =  cache.get(cache_key_choices)
    if not survey_heading_choices:
        survey_heading_choices=list(Choice.objects.all().exclude(active=0).values('id','question_id','text'))
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_choices,survey_heading_choices,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    
    #Caching the all mastelookups 
    cache_key_lookup = INSTANCE_CACHE_PREFIX+'all_master_lookup_caching'
    master_lookup =  cache.get(cache_key_lookup)
    if not master_lookup:
        master_lookup=list(MasterLookUp.objects.all().exclude(active=0).values('id','name','slug'))
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_lookup,master_lookup,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])


#filter and search field replace with actual value
def search_filter_replace(request,query,filters,search_field,address_widget_filter):
    
    filters_query=[]
    # import ipdb;ipdb.set_trace()
    for filter_key,filter_cond in filters.items():
        if int(filter_key) in address_widget_filter:
            selected=request.GET.getlist(filter_key,'')
            selected_val={}
            for idx,i in enumerate(selected):
                if i != '':
                    selected_val.update({str(idx+1):i})
            selected_val=json.dumps(selected_val)
        else:
            selected_val=request.GET.get(filter_key,'').strip()
        filter_cond=filter_cond.replace('@@filter_value',str(selected_val))
        if selected_val != '' and selected_val != '{}':
            filters_query.append(filter_cond)

    for filter_key,filter_cond in search_field.items():
        selected_val=request.GET.get('search','')
        filter_cond=filter_cond.replace('@@filter_value',selected_val.strip())
        if selected_val != '':
            filters_query.append(filter_cond)

    query=query.replace('@@filters',''.join(filters_query))
    return query

# validation for profile page add button hide/show
def add_button_validation_profile(survey,object_lists):
    hide_button=False
    if survey.extra_config.get('add_button_validation'):
        hide_button_logic=survey.extra_config.get('add_button_validation').get('hide_add_button')
        type=survey.extra_config.get('add_button_validation').get('type')
        if hide_button_logic and len(object_lists) > 0:
            if isinstance(object_lists[0],JsonAnswer):
                object_list = model_to_dict(object_lists[0])
            else:
                object_list = object_lists[0]
            response_dict=object_list.get('response')#order_by('-created').first().
            date_select=False
            if survey.extra_config.get('add_button_validation').get('index_order'):
                hide_button_logic={k: hide_button_logic[k] for k in survey.extra_config.get('add_button_validation').get('index_order')}

            for key,value in hide_button_logic.items():
                if type == 'select' and response_dict.get(key) and response_dict.get(key) == hide_button_logic.get(key):
                    hide_button=True
                    break
                elif type == 'date':
                    if date_select and (not response_dict.get(key) or response_dict.get(key) == ''):
                        hide_button=True
                        break
                    elif response_dict.get(key) and response_dict.get(key) == hide_button_logic.get(key):
                        date_select=True
                        #break          
    return hide_button


def get_financial_year_dates():
    from datetime import datetime, timedelta
    # Get the current date
    today = datetime.today()
    
    # Determine the start and end dates based on the current date
    if today.month >= 4:
        # Financial year starts April 1st of the current year
        start_date = datetime(today.year, 4, 1)
        # Financial year ends March 31st of the next year
        end_date = datetime(today.year + 1, 3, 31)
    else:
        # Financial year starts April 1st of the previous year
        start_date = datetime(today.year - 1, 4, 1)
        # Financial year ends March 31st of the current year
        end_date = datetime(today.year, 3, 31)
    
    return start_date.date(), end_date.date()

from django.forms.models import model_to_dict

class WebResponseListing(View):
    template_name = 'survey_forms/form_survey_listing.html'

    def get(self, request, survey_slug=None, school_creation_key=None, school_name=None,creation_key=None):
        survey_key_question,profile_cache_key,cache_survey_id=None,None,{}
        extra_config,profile_obj,object_lists={},None,None
        survey=None
        survey_questions={}
        facilities=''
        request_data=request.GET.dict()
        
        #load_data_to_cache call for if cache cleared
        load_data_to_cache()
        
        #Getting the mapped facility json answer ids from UserFacilityMapping
        #District level user = 29 / State level user = 28 / National level user = 27
        locations=request.session.get('user_boundary_list')

        #Caching the facility ids for the user
        # cache_key_facility = 'faclity_ids_for_user'
        # user_facility_list =  cache.get(cache_key_facility)
        # if not user_facility_list:
        # import ipdb;ipdb.set_trace()
        current_time = datetime.now()
        if request.session.get('user_organizationunit_id') in [29,28] :
            # facilities='or survey_id = 2'
            #added for RC data to show the district only
            rc_json_id =  BeneficiaryResponse.objects.filter(Q(address_2__in = locations) | Q(address_1__in = locations),survey_id=2,active=2).values_list('json_answer_id',flat=True)
            facilities='or js.id in ({0})'.format(str(list(rc_json_id) or ['0'])[1:-1])
            user_role_type_ids=request.session.get('user_role_id')
            #get all the beneficiries based on assigned locations
            if (27 in user_role_type_ids):
                #get json answers created by ppm
                user_facility_list=cache.get(f'{INSTANCE_CACHE_PREFIX}facility_mapping_{request.user.id}')
                if not user_facility_list:
                    user_facility_list=UserFacilityMapping.objects.filter(Q(deactivate_date__gte=current_time) | Q(deactivate_date=None),user_id=request.user.id).exclude(active=0).values_list('json_answer_id',flat=True)
                    cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'SURVEY_LISTING_PAGE',f'{INSTANCE_CACHE_PREFIX}facility_mapping_{request.user.id}',user_facility_list,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
                # user_facility_list=request.session.get('facility_list',[-1])
                facilities=facilities+" or (user_id = {0} and (survey_id in (5,6,7,17) or js.response ->> '616' != '620'))".format(request.user.id)
                # facilities=facilities+" or (s.id = 7 and user_id = {0}) or (js.response ->> '616' != '620' and user_id = {0})".format(request.user.id)
            else:
                user_facility_list=BeneficiaryResponse.objects.filter((Q(address_2__in=locations)|Q(address_1__in=locations)|Q(survey_id=2)),active=2).values_list('json_answer_id',flat=True)
                #boundaries based on user
                boundaries =  load_data_to_cache_boundaries_name()
                district_boundarys=[item.get('id') for item in boundaries if item.get('parent') in locations or item.get('id') in locations] 
                facilities=facilities+" or (survey_id in (7) and js.cluster ->> 'Boundary' in ({0}))".format(str(list(map(str, district_boundarys if district_boundarys else [-1])))[1:-1])

            #js.id in ({0})  or 
            facilities=' and (js.facility_id in ({0}) {1})'.format(','.join(list(map(str, user_facility_list if user_facility_list else [-1]))),facilities)
        # else:
        #     
        # elif request.session.get('user_organizationunit_id') == 28:
        #     user_facility_list=BeneficiaryResponse.objects.filter(active=2,address_1__in=locations).values_list('json_answer_id',flat=True)
        # else:
        #     user_facility_list=JsonAnswer.objects.filter(active=2).values_list('id',flat=True)
            # cache_set_with_namespace('SURVEY_LISTING_PAGE',cache_key_facility,user_facility_list,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
        
        # #Caching the location based json ids for the user
        # cache_key_location_json = 'lcoation_json_ids_for_user'
        # user_location_json_list =  cache.get(cache_key_location_json)
        # if not user_location_json_list:


        

        if creation_key:
            profile_obj = JsonAnswer.objects.get(creation_key=creation_key)
            survey=profile_obj.survey
            fixed_profile_ids=profile_obj.survey.extra_config.get('profile_fields',survey.extra_config.get('header_for_listing',[]))
            profile_cache_key = INSTANCE_CACHE_PREFIX+'survey_heading_questions_for_'+str(survey.id)
            cache_survey_id.update({profile_cache_key:survey.id})
            survey_id = profile_obj.survey
        if survey_slug:
            survey = Survey.objects.get(slug=survey_slug)
            listing_order=survey.extra_config.get('listing_order',['-created'])
            if not creation_key:
                fixed_profile_ids=survey.extra_config.get('profile_fields',survey.extra_config.get('header_for_listing',[]))
                profile_cache_key = INSTANCE_CACHE_PREFIX+'survey_heading_questions_for_'+str(survey.id)
                cache_survey_id.update({profile_cache_key:survey.id})
                survey_id = survey
            

            # if survey.data_entry_level_id == 1:
                # level_obj = BoundaryLevel.objects.get(code=request.session.get('user_boundary_levelcode'))
                # user_locations = user_projects_locations(request.user, level_obj)
                # if request.session.get('user_boundary_levelcode') == 2 :
                #     ben_responses=BeneficiaryResponse.objects.filter(address_2__in = user_locations,survey__slug=survey_slug).order_by('modified')
                # else:
                #     ben_responses=BeneficiaryResponse.objects.filter(address_1__in = user_locations,survey__slug=survey_slug).order_by('modified')
                # ben_responses_ids=ben_responses.values_list('json_answer_id',flat=True) 
                # query='select js.id,survey_id,response,s.slug,creation_key,js.created,js.modified,js.active from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active=2 and s.id = {0} and js.id in ({1}) @@filters order by @@order_by'.format(survey.id,','.join(list(map(str, user_facility_list if user_facility_list else [0]))))
                # object_lists = JsonAnswer.objects.filter(id__in=ben_responses_ids,survey__slug=survey_slug,active=2).values('survey_id','response','survey__slug','creation_key','created','modified','active').order_by(*listing_order)
            # else:
            user_district = list(UserProjectMapping.objects.filter(user_id=request.user.id).values_list('project__district__id',flat=True))
            district=Boundary.objects.filter(active=2,code__in=list(map(str,user_district))).values_list('id',flat=True)

            creation_key_wise_district = "','".join(list(BeneficiaryResponse.objects.filter(address_2__in=district).values_list('creation_key',flat=True)))
            query='select js.id,survey_id,response,s.slug,creation_key,js.created,js.modified,js.active from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id = {0} {1}  @@creation_key @@filters  order by @@order_by'.format(survey.id,facilities,creation_key_wise_district)#@@filters
            if survey.id == 1 and request.user.groups.all()[0].id == 1:
                query='select js.id,survey_id,response,s.slug,creation_key,js.created,js.modified,js.active from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id = {0} {1} and creation_key in (\'{2}\')  @@creation_key @@filters  order by @@order_by'.format(survey.id,facilities,creation_key_wise_district)#@@filters
            if school_creation_key:
                query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and s.id = {0} {1} and js.response->>\'237\'=\'{2}\'  @@creation_key @@filters order by @@order_by'.format(survey.id,facilities,school_creation_key)#@@filters
                # object_lists = JsonAnswer.objects.filter(facility_id__in=request.session.get('facility_list'),survey__slug=survey_slug,active=2).values('survey_id','response','survey__slug','creation_key','created','modified','active').order_by(*listing_order)

            if creation_key:
                query=query.replace("@@creation_key"," and js.cluster->>'BeneficiaryResponse' = '{0}'".format(creation_key))
            else:
                query=query.replace("@@creation_key","")
            
                # object_lists=object_lists.filter(cluster__BeneficiaryResponse=creation_key).order_by('-created')                
            survey_key_question = INSTANCE_CACHE_PREFIX+'survey_heading_questions_for_'+str(survey.id)
            cache_survey_id.update({survey_key_question:survey.id})
        

        #Heading question ids
        cache_key_choices = INSTANCE_CACHE_PREFIX+'survey_heading_question_ids_'+str(survey.id)
        header_ids =  cache.get(cache_key_choices)
        if not header_ids:
            try:
                header_ids=SurveyDisplayQuestions.objects.get(survey_id=survey.id, display_type='0').questions
            except:
                header_ids=Question.objects.filter(block__survey_id=survey.id, parent=None, qtype__in=['T', 'R', 'S', 'C']).exclude(active=0).values_list('id',flat=True)[:5]
            cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_choices,header_ids,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(header_ids)])
        
        # cache_delete_namespace('SURVEY_LISTING_PAGE')

        #Survey listing page headings 
        
        cache_keys=[profile_cache_key,survey_key_question]
        survey_questions =  cache.get_many(cache_keys)
        for i in cache_keys:        
            if i and i not in survey_questions:
                questions = Question.objects.filter(block__survey=cache_survey_id.get(i)).exclude(active=0).values('id','text','qtype','training_config').order_by('question_order')
                cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',i,questions,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
                survey_questions.update({i:questions})
        
        fixed_questions=survey_questions.get(profile_cache_key)
        if fixed_questions:
            preserved_prfile = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fixed_profile_ids)])
            # profile_fields=fixed_questions.filter(id__in=fixed_profile_ids).order_by(preserved_prfile)
            fixed_questions=fixed_questions.filter(parent=None)
            if survey.id == 10:
                school_creation_key = creation_key
            if school_creation_key:
                ans=JsonAnswer.objects.get(creation_key=school_creation_key).response
                profile_fields = question_based_answers(survey_id,ans,fixed_profile_ids)
            elif survey.id != 1:
                ans=JsonAnswer.objects.get(creation_key=profile_obj.response['237']).response
                profile_fields = question_based_answers(survey_id,ans,fixed_profile_ids)
        
        if survey_slug:
            survey_heading_questions=survey_questions.get(survey_key_question)
            survey_heading_questions=survey_heading_questions.filter(id__in=header_ids)#.order_by(preserved)
            
            #filter and searching the listing page
            #### filter and search fields ####
            filters=survey.extra_config.get('filters',{})
            search_field=survey.extra_config.get('search_fields',{})
            address_widget_filter=[]

            if filters:
                filter_all_questions=cache.get(survey_key_question)
                filter_all_choices=cache.get(INSTANCE_CACHE_PREFIX+'survey_listing_page_answer_choices')
                filter_questions=[item for item in filter_all_questions if str(item.get('id')) in list(filters.keys())]

                filter_choices={}
                next_level_boundries=BoundaryLevel.objects.filter(active=2)#code=request.session['user_boundary_levelcode']
                for i in filter_questions:
                    if i.get('qtype') == 'AW':
                        address_widget_filter.append(i.get('id'))
                        boundaries=load_data_to_cache_boundaries_name()
                        boundarys=[item for item in boundaries if (request.user.is_superuser or item.get('id') in request.session.get('user_parent_boundary_list')) and item.get('boundary_level_type_id') == 1 ]
                        request_data.update({str(i.get('id')):request.GET.getlist(str(i.get('id')))})
                    else:
                        choices_dict={}
                        for item in filter_all_choices:
                            if item.get('question_id') == i.get('id'):
                                choices_dict[item.get('id')]=item.get('text')
                        filter_choices[i.get('id')]=choices_dict

                
            filtered_query=search_filter_replace(request,query,filters,search_field,address_widget_filter)
            
            filtered_query=filtered_query.replace('@@order_by','created desc')
            object_lists=JsonAnswer.objects.raw(filtered_query)
            #validation of add button inside the profile page
            button_query=query.replace('@@order_by','created desc limit 1')
            button_query=button_query.replace('@@filters','')
            object_list=JsonAnswer.objects.raw(button_query)

            # import ipdb;ipdb.set_trace()
            #inside the profile page add button validation
            hide_button=add_button_validation_profile(survey,object_list)
            #main listing page button hide 
            main_add_button=survey.extra_config.get('restrict_add',False)

        
        #getting the actions dropdowns from extra config
        options_survey_ids=survey.extra_config.get('action_options',[])
        if survey.id == 10:
            school_creation_key=creation_key
        
        if school_creation_key:
            school_survey= JsonAnswer.objects.get(creation_key=school_creation_key or creation_key)
            school_name=school_survey.response['231']
            options_survey_ids = school_survey.survey.extra_config.get('action_options',[])
        preserved_survey = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(options_survey_ids)])
        
        options_dropdown=Survey.objects.filter(id__in=options_survey_ids).exclude(active=0).order_by(preserved_survey)
        
        heading=profile_obj.survey.name if profile_obj else survey.name

        # partner_creation_key = request.session.get('partner_key')
        # responses = BeneficiaryResponse.objects.none()

        if survey_slug :#and not creation_key:
            #########Pagination##########
            object_lists=web_pagination(request,object_lists)
            page_number_display_count = settings.PAGE_NUMBER_DISPLAY_COUNT
            current_page = request.GET.get('page', 1)
            page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
            page_number_end = page_number_start + page_number_display_count if page_number_start + \
                page_number_display_count < object_lists.paginator.num_pages else object_lists.paginator.num_pages+1
            display_page_range = range(page_number_start, page_number_end)

        ##Hardcoded code for show the status of inmate 
        if creation_key and profile_obj.survey.id == 1 :
            # survey_heading_choices = load_data_to_cache_choices()
            # query="select response->>'574' as known_hiv,response->>'575' as new_hiv,response->>'577' as death_result,response->>'576' as tb_result,response->>'578' as sti_result,response->>'579' as syphilis_result,response->>'580' as hbv_result,response->>'581' as hbv_result,response->>'720' as death_report from survey_jsonanswer where cluster->>'BeneficiaryResponse' = '{0}' or creation_key = '{0}';".format(creation_key)
            # with connection.cursor() as cursor:
            #     cursor.execute(query)
            #     result = cursor.fetchall()
            #     selected_choices=[item for tuple in result for item in tuple]
            #     new_list = list(filter(lambda x: x not in ['',None],selected_choices ))
            # # status_choices=[item.get('text') for item in survey_heading_choices if str(item.get('id')) in new_list]
            # status_text=', '.join(new_list)
            try:
                status_text= ', '.join(eval(profile_obj.response.get('574','[]') or '[]'))
            except:
                status_text=profile_obj.response.get('574','')
        print('number of query excuted:',len(connection.queries),'')
        #request data for filter
        filter_request=request.META['QUERY_STRING']
        filtered_items = [item for item in filter_request.split('&') if not item.startswith('page=')]
        filter_request_data='&'.join(filtered_items)
        print(survey.id,'surveysurvey')
        return render(request,self.template_name,locals())

def load_data_to_cache_choices():
    #caching the choices for forms
    query = "select jsonb_object_agg(question_id, choice_info) from (select a.question_id, jsonb_agg(jsonb_build_object('id',a.id, 'choice',a.text, 'disabled', a.config->'disable', 'skip_question_ids', coalesce(b.skip_list,'[]'::jsonb)) order by a.choice_order) choice_info from survey_choice a left outer join (select choice_id, jsonb_agg(question_id) as skip_list from survey_choice_skip_question group by choice_id ) b on b.choice_id = a.id where a.active != 0  group by question_id ) as x "

    cache_key_choice = INSTANCE_CACHE_PREFIX+'all_choice_cache'
    choice_cache_dict =  cache.get(cache_key_choice)
    if not choice_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            choice_cache_dict = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_choice,choice_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return choice_cache_dict

def load_data_to_cache_survey():
    #caching the surveys
    query1 = "SELECT jsonb_object_agg(id, s_val) FROM ( SELECT a.id, jsonb_build_object('id', a.id, 'name', a.name, 'survey_type', a.survey_type, 'survey_order', a.survey_order, 'slug', a.slug,'short_name', a.short_name, 'extra_config', coalesce(a.extra_config, '[]'::jsonb) ) as s_val FROM survey_survey a WHERE a.active = 2 ) as x"

    cache_key_survey = INSTANCE_CACHE_PREFIX+'all_choice_surveys'
    survey_cache_dict =  cache.get(cache_key_survey)
    if not survey_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query1)
            result = cursor.fetchall()
            survey_cache_dict = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_survey,survey_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return survey_cache_dict


def load_data_to_cache_block():
    #caching the blocks based on survey
    query = "SELECT jsonb_object_agg(survey_id, blocks) FROM ( SELECT a.survey_id, jsonb_agg( jsonb_build_object('id', a.id, 'name', a.name ) ORDER BY a.block_order ) as blocks FROM survey_block a WHERE a.active = 2 GROUP BY survey_id ) as x"

    cache_key_block = INSTANCE_CACHE_PREFIX+'all_survey_blocks'
    block_cache_dict =  cache.get(cache_key_block)
    if not block_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            block_cache_dict = json.loads(result[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_block,block_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return block_cache_dict

def load_data_to_cache_boundarylevel():
    #caching the boundary level

    query = "SELECT jsonb_object_agg(id, b_val) FROM ( SELECT a.id, jsonb_build_object( 'id',a.id,'name', a.name ) AS b_val FROM application_master_boundarylevel a WHERE a.active = 2 ) AS x"

    cache_key_boundary_level = INSTANCE_CACHE_PREFIX+'boundarylevel_meta'
    boundarylevel_cache_dict =  cache.get(cache_key_boundary_level)
    if not boundarylevel_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result2 = cursor.fetchall()
            boundarylevel_cache_dict = json.loads(result2[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_boundary_level,boundarylevel_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return boundarylevel_cache_dict

def load_data_to_cache_boundaries_name():
    #boundaries based on user
    cache_key_boundaries = INSTANCE_CACHE_PREFIX+'all_boundary_caching'
    boundaries =  cache.get(cache_key_boundaries)
    if not boundaries:
        boundaries=list(Boundary.objects.all().exclude(active=0).values('id','name','boundary_level_type_id','parent','code').order_by('name'))
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'BOUNDARY_DATA',cache_key_boundaries,boundaries,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return boundaries
    
from django.shortcuts import redirect
@login_required(login_url='/')
def add_survey_form(request,pk):
    from survey.api_views_version1 import add_survey_answers_version_1

    template_name = 'survey_forms/survey_questions_form.html'
    cached_surveys = load_data_to_cache_survey()
    survey = cached_surveys.get(str(pk))
    # caching the block based on survey id
    blocks =  load_data_to_cache_block()
    blocks = blocks.get(str(pk))
    
    school_creation_key = request.GET.get('creation_key')
    school_name = request.GET.get('school_name')
    heading=survey.get('name')
    skip_questions=[]
    ben_uuid=request.GET.get('ben',request.POST.get('ben'))
    #block for shows the beneficiary details 
    try:
        if ben_uuid:
            benificiary=JsonAnswer.objects.get(creation_key=ben_uuid)
            json_response=benificiary.response
            profile_obj=benificiary
            ben_survey = cached_surveys.get(str(benificiary.survey_id))
            fixed_profile_ids=ben_survey.get('extra_config').get('profile_fields',[])
            ans=json_response
            if benificiary.survey.id != 1:
                ans=JsonAnswer.objects.get(creation_key=json_response['237']).response
            profile_fields = question_based_answers(benificiary.survey_id,ans,fixed_profile_ids)
        else:
            json_response={}
        #Hardcoded code for show the status of inmate 
        if ben_uuid and profile_obj.survey_id == 1 :
            # survey_heading_choices = load_data_to_cache_choices()
            # query="select response->>'574' as known_hiv,response->>'575' as new_hiv,response->>'577' as death_result,response->>'576' as tb_result,response->>'578' as sti_result,response->>'579' as syphilis_result,response->>'580' as hbv_result,response->>'581' as hbv_result,response->>'720' as death_report from survey_jsonanswer where cluster->>'BeneficiaryResponse' = '{0}' or creation_key = '{0}';".format(ben_uuid)
            # with connection.cursor() as cursor:
            #     cursor.execute(query)
            #     result = cursor.fetchall()
            #     selected_choices=[item for tuple in result for item in tuple]
            #     new_list = list(filter(lambda x: x not in ['',None],selected_choices ))
            # status_choices=[item.get('text') for item in survey_heading_choices if str(item.get('id')) in new_list]
            try:
                status_text= ', '.join(eval(profile_obj.response.get('574','[]') or '[]'))
            except:
                status_text=profile_obj.response.get('574','')
    except Exception as e:
        error_msg =e.args[0]
        logging.error(error_msg)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(error_stack)
        json_response={}
    
    #Based on the skip questions hide questions inside the grid 
    if survey.get('extra_config').get('skip_question') and json_response:
        config=survey.get('extra_config').get('skip_question')
        for k,v in config.items():
            skip_questions.extend(config.get(k).get(json_response.get(k)))

    #survey 8 logic : based on parent questions , child question answer will store
    if pk == '8' and json_response:
        questions_meta = load_data_to_cache_questions()
        skip_hiv_questions = questions_meta.get('563')#Question.objects.filter(id=563)
        if skip_hiv_questions and skip_hiv_questions.get('training_config'):
            reference_id=skip_hiv_questions.get('training_config').get('reference_id')
            result=skip_hiv_questions.get('training_config').get('result')
            ans_append=False
            for qid, ans in reference_id.items():
                if json_response.get(qid) == ans:
                    ans_append = True
                else:
                    ans_append= False
            if ans_append:
                value=result.get('success').get('text')
            else:
                value=result.get('fail').get('text')
        
        #static code for if the survey have records or not 
        count_of_hiv_records=len(JsonAnswer.objects.filter(cluster__BeneficiaryResponse=ben_uuid,survey_id=8))

        # gender based field for hiv form hide the question In Case of PPW inmate Linked with PPTCT
        gender_male=False
        if json_response.get('9') == '65':
            gender_male=True
    boundaries = load_data_to_cache_boundaries_name()
    if not request.user.is_superuser and not request.user.is_staff:
        next_level_boundries=load_data_to_cache_boundarylevel()
        boundarys=[item for item in boundaries if item.get('boundary_level_type_id') == 1 and item.get('code') in list(map(str, request.session['user_parent_boundary_list']))] 

    # cached dict values of choices
    cache_key_choice = INSTANCE_CACHE_PREFIX+'all_choice_cache'
    choice_cache_dict =  cache.get(cache_key_choice) 

    if request.method  == 'POST':
        
        # Condition for custom page of weekly inmate data report
        if request.POST.get('continue'):
            previous_form_data=request.POST.dict()
        else:
            now = datetime.now()
            date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            answers=json.loads(request.POST.getlist('all_in_one')[0])
            ben_uuid=request.GET.get('ben',request.POST.get('ben','0'))
            responses={
                "u_uuid": request.user.id,
                "d_uuid": "",
                "pushInput": [
                    {
                    "r_uuid": "",
                    "survey_id": pk,
                    "last_updated_date": date_time_str,
                    "beneficiary_id": ben_uuid,
                    "cluster_id": request.POST.get('cluster_id'),
                    "answers_array":str(answers),
                    }]
            }
            # ans=json.loads(request.POST.get('all_in_one'))
            content=add_survey_answers_version_1(request,**responses)
            logger.info('Data sent to database from web:' ,json.loads(content.content.decode('utf-8')))
            result=json.loads(content.content.decode('utf-8'))
            if not result['status'] or result['sync_res'][0]['sync_status'] != 2:
                return render(request,template_name,locals())
            # survey=Survey.objects.get(id=pk)
            if ben_uuid != '0':
                profile_url=f'/configuration/profile/{survey.get("slug")}/{ben_uuid}/'
            elif school_creation_key:
                ben_uuid=result['u_uuid']
                profile_url=f'/configuration/profile/{ben_uuid}/'
            else:
                profile_url = f'/configuration/list/{survey.get("slug")}/'
            return HttpResponseRedirect(profile_url)
    return render(request,template_name,locals())


def prepare_data(response_data,ben_uuid,json_id,type):
    return_data=[]
    for data in response_data:
        if type == 'cluster_beneficiry' and data.get('cluster__BeneficiaryResponse') == ben_uuid:
            return_data.append({'id':data.get('id'),'response':data.get('response')})
        elif type == 'unique_validation' and str(data.get('id')) != str(json_id):
            return_data.append({'response':data.get('response')})
    return return_data

def partner_registration_date_validate(error_msg,resp_dict,ben_respons,previous_record_validation,field_key,month_format,survey_id,validations,error_field):
    ben_subhiksha_register_date=ben_respons.get(field_key,ben_respons.get('75'))
    date_entered=resp_dict.get(previous_record_validation.get(survey_id),resp_dict.get('120'))
    if date_entered and month_format.match(date_entered) and ben_subhiksha_register_date :
        date_entered='01-'+date_entered
        ben_subhiksha_register_date="01"+ben_subhiksha_register_date[2:]
    if ben_subhiksha_register_date and date_entered and datetime.strptime(date_entered, "%d-%m-%Y") < datetime.strptime(ben_subhiksha_register_date, "%d-%m-%Y"):
        error_msg[previous_record_validation.get(survey_id)]="{0} should be greater than {1}".format(validations.get(survey_id).get(previous_record_validation.get(survey_id)).get('field'),error_field)
        
    return error_msg

def custom_validation_survey_wise(resp_dict,survey_id,json_id,ben_uuid=None):

    #this function return the error in any custom validations fails
    error_msg = {}
    json_id=str(json_id)
    validations={
        1:{
            "8":{"field":"Inmate Date of Birth "},
            # "35":{"field":"when was the last time you took (inhale/smoke/ingested) the drugs"},
            "40":{"field":"When was the last time you had any type of sex","validate_with":"8"},
            # "42":{"field":"when was you forced to have sex","validate_with":"8"},
            "16":{"field":"Date of Imprisonment","validate_with":"8"},
            "4":{"field":"Date of registration in Subhiksha+ "},
            # "35":{"field":"when was the last time you took (inhale/smoke/ingested) the drugs"},
            # "40":{"field":"When was the last time you had any type of sex"},
            # "42":{"field":"when was you forced to have sex"},
            "21":{"field":"Expected date/year of release"},
        },
        3:{
            "58":{"field":"DOB"},
            "64":{"field":"Date of Selection"},
            "65":{"field":"Date of Training"},
            "556":{"field":"Date of 1st Refresher Training"},
            "557":{"field":"Date of 2nd Refresher Training"},
            "66":{"field":"Date of Release"},
        },
        # 7:{
        #     "98":{"field":"Date of activity organized"},
        #     "107":{"field":"Date of Advocacy Meeting"},
        # },
        8:{
            "120":{"field":"Date of HIV screening"},
            "121":{"field":"Date when found screened reactive"},
            "123":{"field":"Date of HIV confirmation test"},
            "128":{"field":"Date of Pre-ART registration" ,"validate_with":"123"},
            "131":{"field":"Date of Baseline CD-4 Test","validate_with":"123"},
            "132":{"field":"Date of ART initiation ","validate_with":"123"},
            "136":{"field":"Date of Viral load test","validate_with":"123"},
            "140":{"field":"If yes, date of Linkages with PPTCT","validate_with":"123"},
        },
        9:{
            "141":{"field":"Date of TB Screening (4S)"},
            "143":{"field":"Date of tested for TB "},
            "147":{"field":"Date of ATT initiation"},
            "149":{"field":"Date of linkages with Nikshay"},
            "151":{"field":"Date of completion of ATT"},
        },
        10:{
            "152":{"field":"Date of STI Screening"},
            "156":{"field":"Date of episodic treatment completed"},
        },
        11:{
            "157":{"field":"Date tested for Syphilis"},
            "160":{"field":"Date of episodic treatment completed"},
        },
        12:{
            "161":{"field":"Date tested for HBV"},
            "163":{"field":"Date of initiated HBV Treatment"},
            "164":{"field":"Date of completed HBV Treatment"},
        },
        13:{
            "165":{"field":"Date tested for HCV"},
            "167":{"field":"Date of initiated HCV Treatment"},
            "168":{"field":"Date of completed HCV Treatment"},
        },
        14:{
            "171":{"field":"Spouse/Partner Date of birth"},
            "173":{"field":"Date of HIV Screening"},
            "572":{"field":"Date of First Repeat HIV screening"},
            "174":{"field":"Date of HIV Confirmation"},
            "177":{"field":"Date of ART initiation"},
            "181":{"field":"Date of baseline CD-4 Test"},
        },
        15:{
            "198":{"field":"Date of follow-up/visit"},
        },
        16:{
            "209":{"field":"Date of linkages with Scheme"},
        },
        17:{
            "225":{"field":"Date of establishment"},
            "227":{"field":"Date of making functional"},
            "229":{"field":"Date of making non-functional"},
        },
        18:{
            "256":{"field":"Reporting Month"},
        },
        20:{
            "293":{"field":"Reporting Month"},
            "294":{"field":"Start Date"},
            "295":{"field":"End Date"},
        },
        141:{
            "184":{"field":"Child Date of birth"},
            "186":{"field":"Date of HIV Screening"},
            "573":{"field":"Date of First Repeat HIV screening"},
            "187":{"field":"Date of HIV Confirmation"},
            "190":{"field":"Date of ART initiation"},
            "194":{"field":"Date of baseline CD-4 Test"},
        },
        161:{
            "217":{"field":"Date of linkages"},
        },
        162:{
            "223":{"field":"Date of death"},
        },
    }
    previous_record_validation={
        1:'4',#Date of registration in Subhiksha+
        # 3:'64',
        8:'123',#'120',# Date of HIV screening
        9:'141',#Date of TB Screening (4S)
        10:'152',#Date of STI Screening
        # 10:'156',
        11:'157',#Date tested for Syphilis
        12:'161',#Date tested for HBV
        13:'165',#Date tested for HCV
        15:'198',#Date of follow-up/visit
        # 16:'209',
        # 17:'225',
        18:'256',#Reporting Month(MM/YY)
        20:'293',#Reporting Month(MM/YY)
        # 161:'217',
        # 162:'223',
    }
    # if the conditon key and value will match then the key will pass as the key for resp_dict
    # conditional_date_range_checking={
    #     8:{'key':'8','condition':{'5':'275'},'field':'Date of birth','update_id':'123'},#8:Date of birth 5:Inmate Registered as 275:Known HIV Positive
    # }
    unique_validation={
        1:{"6":"Inmate UID"},
        2:{"47":"Name of Health Service Centre","address,1,45,2":"District","48":"Address","49":"Type of Services"},        
        4:{"235":"Name of Prison/OCS","241":"Place","address,1,69,2":"District"},
        "messages":{
            1:"Unable to generate the uid for this facility. Please contact administrator"
        }
    }
    beneficiary_unique_validation={
        3:{"57":"Name of PPV"},
        18:{"256":"Reporting Month(MM/YY)"},
        20:{"293":"Reporting Month","294":"Start Date"},
        "messages":{
            20:"Data has already exists on web for the selected dates. Please delete this record,sync,recheck before entering data.",
            18:"Data has already exists on web for the selected dates. Please delete this record,sync,recheck before entering data."
        }
    }

    inline_validations={
        8:{
            "54":{
                "131":{"field":"Date of CD-4 Test","validation_question":"128","message":"Date of CD-4 Test should be greated than Date of ART registration","all_field_mandatory":"130"},
            },
            "119":{
                "136":{"field":"Date of Viral load test","validation_question":"128","message":"Date of Viral load test should be greated than Date of ART registration","all_field_mandatory":"137"},
            }
        },
    }

    # validation for checking the mandatory fields values are exists or not
    # questions = load_data_to_cache_survey_based_questions().get(str(survey_id))
    # questions_for_mit_prison=["256","293","294","295"]
    # error_msg = {i['id']:f'{i["text"]} is required ' for i in questions_for_mit_prison if i.get('mandatory') and resp_dict.get(str(i.get('id'))) in ['',None]}
    questions_for_mit_prison = validations.get(survey_id) if survey_id in [18,20] else {}
    error_msg = {q_id:f'{text["field"]} is required ' for q_id,text in questions_for_mit_prison.items() if resp_dict.get(q_id) in ['',None]}
    
    if error_msg:
        return error_msg
    
    response_data=JsonAnswer.objects.filter(active=2,survey_id=survey_id).values('id','survey_id','cluster__BeneficiaryResponse','response').order_by('-created')
    ben_respons={}
    if ben_uuid not in ['None','0',None]:
        ben_respons=JsonAnswer.objects.get_or_none(creation_key=ben_uuid).response
    # for surveyid,validations in validations.items():
    if previous_record_validation.get(survey_id):
        month_format = re.compile(r'\d{1,2}-\d{4}')
        date_format = re.compile(r'\d{1,2}-\d{1,2}-\d{4}')
        #return data need for unique and other validations
        data=prepare_data(response_data,ben_uuid,json_id,'cluster_beneficiry')
        if len(data) == 0 or str(data[len(data) - 1].get('id')) == json_id:

            # commented the above line becuase of this ticket : https://pm.thesocialbytes.com/issues/19847
            field_key='4'
            error_field = 'Date of registration in Subhiksha+'
            #TODO: previously this is dynamic checking . Only for HIV form commented the below code 
            # if conditional_date_range_checking.get(survey_id):
            #     validation_keys=list(conditional_date_range_checking.get(survey_id).get('condition').items())
            #     if ben_respons.get(validation_keys[0][0]) == validation_keys[0][1]:
            #         error_field = conditional_date_range_checking.get(survey_id).get('field')
            #         field_key = conditional_date_range_checking.get(survey_id).get('key')
            #         #if known hiv positive then update the question id for previous_record_validation
            #         update_key = conditional_date_range_checking.get(survey_id).get('update_id')
            #         if not resp_dict.get(conditional_date_range_checking.get(survey_id).get('update_id',previous_record_validation.get(survey_id))):
            #             # field_key = '8' #Date of birth
            #             update_key = '128' #Date of ART registration
            #         previous_record_validation.update({survey_id:update_key})
            if survey_id == 8:
                if ben_respons.get('5') == "275":
                    error_field = "Date of birth"
                    field_key = "8"
                    #if known hiv positive then update the question id for previous_record_validation
                # if not resp_dict.get(update_key,previous_record_validation.get(survey_id)):
                #     update_key = '128' #Date of ART registration
            
            error_msg = partner_registration_date_validate(error_msg,resp_dict,ben_respons,previous_record_validation,field_key,month_format,survey_id,validations,error_field)
            # ben_subhiksha_register_date=ben_respons.get(field_key,ben_respons.get('75'))
            # date_entered=resp_dict.get(previous_record_validation.get(survey_id))
            # # ben_subhiksha_register_date=ben_respons.get('4')
            # if date_entered and month_format.match(date_entered) and ben_subhiksha_register_date :
            #     date_entered='01-'+date_entered
            #     ben_subhiksha_register_date="01"+ben_subhiksha_register_date[2:]
            # if ben_subhiksha_register_date and date_entered and datetime.strptime(date_entered, "%d-%m-%Y") < datetime.strptime(ben_subhiksha_register_date, "%d-%m-%Y"):
            #     error_msg[previous_record_validation.get(survey_id)]="{0} should be greater than {1}".format(validations.get(survey_id).get(previous_record_validation.get(survey_id)).get('field'),error_field)
        
        update_key = "120"
        if survey_id == 8 and not resp_dict.get(previous_record_validation.get(survey_id)):
            previous_record_validation.update({survey_id:update_key})
            update_key = "123"
        if not error_msg:
            for idx,response in enumerate(data):
                prev_rec_idx=None
                next_rec_idx=None
                if json_id == '0':
                    prev_rec_idx=0
                elif json_id == str(response.get('id')):
                    prev_rec_idx=idx+1
                    next_rec_idx=idx-1

                q_id=previous_record_validation.get(survey_id)
                #added the condition for check the field values is added or not
                #if any question is non mandatory
                # import ipdb;ipdb.set_trace()
                if resp_dict.get(q_id) and date_format.match(resp_dict[q_id]): #and not (str(survey_id) in ['20','18'] and resp_dict.get('256',resp_dict.get('293')) in ['10-2023'] )
                    entered_data=resp_dict.get(q_id,resp_dict.get(update_key)) #"02-"+resp_dict[q_id] if month_format.match(resp_dict[q_id]) else resp_dict[q_id]
                    if prev_rec_idx != None and prev_rec_idx < len(data) :
                    #     previous_start_date = '01-' if survey_id == 20 else '03-'
                        # prev_data=data[prev_rec_idx]['response'][q_id]
                        previous_response = data[prev_rec_idx].get('response')
                        prev_data=previous_response.get(q_id,previous_response.get(update_key))  
                        #previous_start_date+data[prev_rec_idx]['response'][q_id] if month_format.match(resp_dict[q_id]) else data[prev_rec_idx]['response'][q_id] 
                    if next_rec_idx != None and next_rec_idx >= 0:
                        # next_data=data[prev_rec_idx]['response'][q_id] #"01-"+data[next_rec_idx]['response'][q_id] if month_format.match(resp_dict[q_id]) else data[next_rec_idx]['response'][q_id]
                        next_response = data[next_rec_idx].get('response')
                        next_data=next_response.get(q_id,next_response.get(update_key)) #"01-"+data[next_rec_idx]['response'][q_id] if month_format.match(resp_dict[q_id]) else data[next_rec_idx]['response'][q_id]
                    
                    # entered data is user intered data and prev_data is previous record date 
                    # if the survey is 20 then previous_start_date is 03- else 01- 
                    if prev_rec_idx != None and prev_rec_idx < len(data) and entered_data and prev_data and datetime.strptime(entered_data, "%d-%m-%Y") < datetime.strptime(prev_data, "%d-%m-%Y"):
                        error_msg[q_id]="{0} should be greater than previous {0} ".format(validations.get(survey_id).get(q_id).get('field'))
                        break
                    if next_rec_idx != None and next_rec_idx >= 0 and entered_data and next_data and datetime.strptime(entered_data, "%d-%m-%Y") > datetime.strptime(next_data, "%d-%m-%Y"):
                        error_msg[q_id]="{0} greater than record already exist ".format(validations.get(survey_id).get(q_id).get('field'))
                        break
    default_validations={
        (8,141,162):{ "8":"Date of Birth"},
        (11,12,13,16,15,161,10,9):{ "4":"Date of registration in Subhiksha+"},
    }
    if validations.get(survey_id):
        previous_item=None
        for key,value in validations.get(survey_id).items():
            default_validation = multi_key_dict_get(default_validations,int(survey_id)) or '0'
            if value.get('validate_with') :
                previous_item=value.get('validate_with')
            curr_date=resp_dict.get(key)
            prev_date=resp_dict.get(previous_item,ben_respons.get(list(default_validation)[0])) 
            date_format = re.compile(r'\d{2}-\d{2}-\d{4}')
            if prev_date and curr_date and date_format.match(curr_date) and date_format.match(prev_date) and datetime.strptime(curr_date, "%d-%m-%Y") < datetime.strptime(prev_date, "%d-%m-%Y"):
                if not resp_dict.get(previous_item):
                    message = list(default_validation.items())[0][1]
                else:
                    message=validations.get(survey_id).get(previous_item).get('field')
                error_msg[key]="{0} should be greater than {1}".format(value.get('field'),message)
                break
            if curr_date:
                previous_item=key 

    if survey_id == 1 and resp_dict.get('6','') == '':
        resp_dict,seq_error=sequence_id_creator(str(survey_id),resp_dict)  
        if seq_error:
            error_msg.update(seq_error)

    if unique_validation.get(survey_id) or beneficiary_unique_validation.get(survey_id):
        # import ipdb;ipdb.set_trace()

        #return data need for unique and other validations
        if unique_validation.get(survey_id):
            data=prepare_data(response_data,ben_uuid,json_id,'unique_validation')
            items=unique_validation.get(survey_id)
            messages=unique_validation.get("messages",{})
            # item_keys=unique_validation.get(survey_id).keys()
        else:
            data=prepare_data(response_data,ben_uuid,json_id,'cluster_beneficiry')
            items=beneficiary_unique_validation.get(survey_id)
            #deleting the editing record from data 
            for idx,i in enumerate(data):
                if str(i.get('id')) == str(json_id):
                    data.pop(idx)
            # item_keys=beneficiary_unique_validation.get(survey_id)
            messages=beneficiary_unique_validation.get("messages",{})

        date_format = re.compile(r'\d{1,2}-\d{1,2}-\d{4}')
        month_format = re.compile(r'\d{1,2}-\d{4}')

        # data=response_data.values('response').exclude(id=json_id)
        for response in data:
            result,error,duplicate={},[],True

            for key_1,value_1 in items.items():
                keys=key_1.split(",")
                exist=getFromDict(response.get('response'),keys)
                val=getFromDict(resp_dict,keys)
                result.update({key_1:[val.lower().strip(),exist.lower().strip()]})
                if (date_format.match(val) or month_format.match(val)) and duplicate:
                    date_pattern='%d-%m-%Y' if date_format.match(val) else '%m-%Y'
                    exist=datetime.strptime(exist,date_pattern)
                    val=datetime.strptime(val,date_pattern)
                    if val == exist:
                        error.append(value_1)
                        duplicate=True
                    else:
                        duplicate=False
                        error=[]
                        break
                elif val.lower().strip() == exist.lower().strip() and duplicate:
                    duplicate=True
                    error.append(value_1)
                else:
                    duplicate=False
                    error=[]
                    break
            
            if error:
                # keys=unique_validation.get(survey_id).keys()
                error_msg[list(items.keys())[0]]=messages.get(survey_id,'{0} together should be unique'.format(', '.join(error)))
            
    if inline_validations.get(survey_id):
        # import ipdb;ipdb.set_trace()
        for key,value in inline_validations.get(survey_id).items():
            if resp_dict.get(key):
                sorted_answer = sorted(resp_dict.get(key).items(), key=lambda x: int(x[0]))
                previous_item=None
                for index,item in sorted_answer:
                    for id,message in value.items():
                        name="group-"+key+str([int(index)])+str([int(id)])
                        error_mes = message.get('message')
                        validation_date_text = resp_dict.get(message.get('validation_question'))
                        if not validation_date_text:
                            validation_date_text = ben_respons.get('8') #8 = Date of Birth
                            error_mes = 'Date should be greated than Date of Birth'
                        if item.get(id) and message.get('validation_question') and validation_date_text and datetime.strptime(item.get(id).strip(), "%d-%m-%Y") < datetime.strptime(validation_date_text.strip(), "%d-%m-%Y") :
                            error_msg[name]={"inline":True,"message":error_mes}
                            break
                    
                        if item.get(id) and previous_item and datetime.strptime(item.get(id).strip(), "%d-%m-%Y") < datetime.strptime(previous_item.strip(), "%d-%m-%Y"):
                            inline={"inline":True,"message":"{0} should be greater than previous {1}".format(message.get('field'),value.get(id).get('field'))}
                            error_msg[name]=inline
                            break
                        if item.get(id):
                            previous_item=item.get(id)
                        
                        # validation if one field data entered and not entered the other field value 
                        field_to_check = message.get('all_field_mandatory') 
                        if bool(item.get(field_to_check)) != bool(item.get(id)):
                            if bool(item.get(id)):
                                name="group-"+key+str([int(index)])+str([int(field_to_check)])
                            error_msg[name]={"inline":True,"message":"Please enter all values to save the record"}
                            break
                    

          
    if survey_id == 8:
        rc_data=prepare_data(response_data,ben_uuid,json_id,'cluster_beneficiry')

        #checking the hiv positive & positive record already exists or not
        for idx,response in enumerate(rc_data):
            if idx==0:
                recent_record=response.get('id')
            if str(response.get('id')) != json_id and response['response'].get('126') and response['response']['126'] == '441' and resp_dict.get('126') == '441' :
                error_msg['126']="Positive record already exists. Please enter valid data" 
                break
            if json_id != '0' and str(recent_record) != json_id and resp_dict.get('126') == '441':
                error_msg['126']="Can't make this record positive. Please enter valid data" 
                break
    if survey_id in [1,3] and ben_uuid != 'None':
        ben_respons=JsonAnswer.objects.get(creation_key=ben_uuid).response
        dob = datetime.strptime(resp_dict.get('8',resp_dict.get('58')), "%d-%m-%Y")
        seventeen_delta = datetime.today().date() - relativedelta(years=17)
        thirteen_delta = datetime.today().date() - relativedelta(years=13)
        if ben_respons.get('72') == "368" and seventeen_delta < dob.date():
            key='8' if resp_dict.get('8') else '58'
            error_msg[key]="Date of birth should be greater than 17 years"
        elif survey_id == 3 and ben_respons.get('72') == "369" and thirteen_delta < dob.date():
            error_msg['58']="Date of birth should be greater than 13 years"
    
    comparing_validation={
        #72: Type of Facility
        #89 : Prison registered in eprison portal
        #368 : Prison
        #369 : OCS
        #384 : Yes
        #385 : No
        #if prison is selected then the Q89 should be 384 or 385 
        4:{"72":{"368":{"89":["384","385"],"message":"Please recheck the type of facility selection"},"369":{"89":['0','',None],"message":"Please enter a valid answer"}},"type":"S"},

        #173,186: Date of first HIV Screening/Test
        #669,670: Type of Test Conducted?
        #654,653: Was repeat test done ?
        14:{"173":{"in":{"condition":{"654":["0","",None],"669":["0","",None]},"message":"Please select valid option"}},"type":"D"},
        141:{"186":{"in":{"condition":{"653":["0","",None],"670":["0","",None]},"message":"Please select valid option"}},"type":"D"},

        # #163,167 : Date of initiated HBV Treatmen
        # #164,168 : Date of completed HBV Treatment
        # 12:{"164":{"in":{"condition":{"164":["",None]},"message":"Please select valid date"}},"type":"D"},
        # 13:{"167":{"in":{"condition":{"168":["",None]},"message":"Please select valid date"}},"type":"D"},

        #9: Gender
        #10 : Marital Status
        #66 : Female
        #65 : Male
        #67 : Transgender
        #289 : Widow
        #290 : Widower
        #287 : Married
        #288 : Unmarried
        #291 : Separated
        1:{"9":{"65":{"10":["290","287","288","291"],"message":"Please recheck the gender and marital status"},"66":{"10":["289","287","288","291"],"message":"Please recheck the gender and marital status"},"67":{"10":["290","289","287","288","291"],"message":"Please recheck the gender and marital status"}},"type":"S"},
    }
    for comparing_question_id,value in comparing_validation.get(survey_id,{}).items():
        for key_1,value_1 in value.items():
            if comparing_validation.get(survey_id,{}).get('type') == 'S':
                comparing_q,comparing_message = value.get(resp_dict.get(comparing_question_id)).items()
                if resp_dict.get(comparing_q[0]) not in comparing_q[1]:
                    error_msg[comparing_q[0]]=comparing_message[1]
                    break
            elif comparing_validation.get(survey_id,{}).get('type') == 'D':
                cond,message = value_1.items()
                operator = key_1 if resp_dict.get(comparing_question_id) not in ['',None] else 'not in'
                for cond_k,cond_v in cond[1].items():
                    if eval(f"{resp_dict.get(cond_k)!r} {operator} {cond_v!r}"):
                        error_msg[cond_k]=message[1]

        #break added because ignore the "type" loop            
        break        
    
    hbv_hcv_validation_date = {
        #163,167 : Date of initiated HBV Treatmen
        #164,168 : Date of completed HBV Treatment
        12:{"164":{"in":{"condition":{"163":["",None]},"message":"Please select valid date"}},"type":"D"},
        13:{"168":{"in":{"condition":{"167":["",None]},"message":"Please select valid date"}},"type":"D"},

    }
    for comparing_question_id,value in hbv_hcv_validation_date.get(survey_id,{}).items():
        for key_1,value_1 in value.items():
            # if hbv_hcv_validation_date.get(survey_id,{}).get('type') == 'S':
            #     comparing_q,comparing_message = value.get(resp_dict.get(comparing_question_id)).items()
            #     if resp_dict.get(comparing_q[0]) not in comparing_q[1]:
            #         error_msg[comparing_q[0]]=comparing_message[1]
            #         break
            if hbv_hcv_validation_date.get(survey_id,{}).get('type') == 'D' and resp_dict.get(comparing_question_id):
                cond,message = value_1.items()
                operator = key_1 #if resp_dict.get(comparing_question_id) #not in ['',None] else 'not in'
                for cond_k,cond_v in cond[1].items():
                    if eval(f"{resp_dict.get(cond_k)!r} {operator} {cond_v!r}"):
                        error_msg[cond_k]=message[1]
        break  
    dob_validation_for_grid={
        # 1:["18","27","30","35","40","42"],
        1:["740","741","742","743","744","745"],
        #740:Sentencing Period in case of CV 
        #743:If yes, when was the last time you took (inhale/smoke/ingested) the drugs
        #742:If yes, how long have you been injecting drugs
        #741:When was the last time you injected drugs
        #744:If yes, when was you forced to have sex
        #745:When was the last time you had any type of sex
    }
    if dob_validation_for_grid.get(survey_id):
        current_date = datetime.now()
        dob = datetime.strptime(resp_dict.get('8'), "%d-%m-%Y")
        age = current_date.year - dob.year - ((current_date.month, current_date.day) < (dob.month, dob.day))
        json_string = json.dumps(resp_dict)
        
        for i in dob_validation_for_grid.get(survey_id):
            pattern = fr'"{i}": "(.*?)"'
            match = re.search(pattern, json_string)
            if match and match.group(1) and  age < int(match.group(1)):
                error_msg[i]="Years should be lesser than age"
                break

    # Prison/OCS Progress start date checking , if perticular facility on selected month if its first record then start date should be 1
    if survey_id == 20 and json_id == '0':
        data=prepare_data(response_data,ben_uuid,json_id,'cluster_beneficiry')
        selected_month = datetime.strptime(resp_dict.get('293'), '%m-%Y')
        filtered_data = [i for i in data if datetime.strptime(i.get('response').get('293'), '%m-%Y') == selected_month]
        selected_start_date = datetime.strptime(resp_dict.get('294'), '%d-%m-%Y')
        if not filtered_data and selected_start_date.date() != selected_month.date():
            error_msg['294'] = 'Start date should be 1st of month'
        elif filtered_data:
            sorted_data = sorted(filtered_data, key=lambda x: datetime.strptime(x["response"]["294"], "%d-%m-%Y"))
            previouse_end_date = datetime.strptime(sorted_data[-1]['response']['295'], '%d-%m-%Y')
            next_date = previouse_end_date + timedelta(days=1)
            if next_date.date() != selected_start_date.date(): 
                error_msg['294'] = 'Start date not matching with previous end date'

    if survey_id in [18,20]:
        error_msg = partner_registration_date_validate(error_msg,resp_dict,ben_respons,previous_record_validation,'75',month_format,survey_id,validations,'Date of registration in Subhiksha+')

    return error_msg

def question_answer_dict(questions,answers_list,response_created_on=None,user=None):
    from .api_views_version1 import convert__to_localdate
    resp_dict ={}
    mandatory_error={}
    address_questions = questions.filter(address_question=True, active=2).exclude(qtype="AW")
    

    for ques in questions:
        if response_created_on and  ques.active == 3 and convert__to_localdate(ques.deactivated_date) < response_created_on:
            pass
        else:
            try:
                #if logic check the any question not in answer_list because of skip logic
                if answers_list.get(str(ques.id)):
                    if ques.qtype == 'D':
                        date_str=list(answers_list.get(str(ques.id))[0].values())[0].replace('\\/','-')
                        # import ipdb;ipdb.set_trace()
                        if date_str and date_str != 'Pick Date':
                            date_fmt = date_str.split('-')
                            date_fmt.reverse()
                            date_rev = '%02d' % int(date_fmt[1]) + '-'+ date_fmt[0] if len(date_fmt) == 2 else '%02d' % int(date_fmt[2]) +'-'+ '%02d' % int(date_fmt[1]) + '-'+ date_fmt[0]
                            resp_dict[str(ques.id)] = date_rev
                    elif ques.qtype in ['S','R']:
        #                if ques.is_other_question():
                        data_list = literal_eval(str(list(answers_list.get(str(ques.id))[0].keys())))
                        for kl in data_list:
                            if len(kl.split("_")) == 4:
                                di_dict = resp_dict.get('other') if resp_dict.get('other') else {}
                                inner_dict = {}
                                inner_dict.update({kl.split("_")[3]: answers_list.get(str(ques.id))[0].get(kl)})
                                di_dict.update({str(ques.id): inner_dict})
                                resp_dict.update({"other": di_dict})
                            else:
                                resp_dict[str(ques.id)]=str(list(answers_list.get(str(ques.id))[0].values())[0])
        #                else:
        #                    resp_dict[str(ques.id)]=str(answers_list.get(str(ques.id))[0].values()[0])
                    elif ques.qtype in ['AW']:
                        ques_dict = {}
                        ques_dict[str(ques.id)] = [dict([a, str(x)] for a,x in answers_list.get(str(ques.id))[0].items())][0]
                        try:
                            for address in address_questions:
                                if list(answers_list.get(str(address.id))[0].values())[0]:
                                    ques_dict.update({str(address.id): str(list(answers_list.get(str(address.id))[0].values())[0])})
                        except:
                            pass
                        final_dict = {'1':ques_dict }
                        resp_dict["address"] = final_dict
                    elif ques.qtype in ['AI']:
                        data_list = literal_eval(str(list(answers_list.get(str(ques.id))[0].keys())))
                        for kl in data_list:
                            if len(kl.split("_")) == 4:
                                di_dict = resp_dict.get('other') if resp_dict.get('other') else {}
                                inner_dict = {}
                                inner_dict.update({kl.split("_")[3]: answers_list.get(str(ques.id))[0].get(kl)})
                                di_dict.update({str(ques.id): inner_dict})
                                resp_dict.update({"other": di_dict})
                            else:
                                #as ajay sir suggestion commented this code 
                                # try:
                                #     resp_dict[str(ques.id)] = str(JsonAnswer.objects.get(creation_key=answers_list.get(str(ques.id))[0].get(kl)).get_beneficiary_object().id)
                                # except:
                                resp_dict[str(ques.id)] = str(answers_list.get(str(ques.id))[0].get(kl))
                    elif ques.qtype in ['GD','In']:
                        ques_final_dict = {}
                        all_question_dict = {}
                        for i in answers_list.get(str(ques.id)):
                            all_question_dict.update(i)
                        response_unique_keys = list(set([item.split('_')[1] for item in all_question_dict.keys()]))
                        for individual_key in response_unique_keys:
                            individual_response = {}
                            for individual_key_content, value in all_question_dict.items():
                                if individual_key == individual_key_content.split("_")[1]:
                                    individual_response.update({individual_key_content.split("_")[2]: value})
                            ques_final_dict.update({individual_key: individual_response})
                        resp_dict[str(ques.id)] = ques_final_dict
                    # elif ques.qtype == 'H':
                    #     # import ipdb;ipdb.set_trace()

                    #     try:
                    #         refered_keys=ques.api_json.get('reference')
                    #         if refered_keys:
                    #             # if refered_keys.get('multiple'):
                    #             assign_val=False
                    #             for key,val in refered_keys.get('condition').items():
                    #                 val_question=questions.get(id=key)
                    #                 answer=list(answers_list.get(str(key))[0].values())[0]
                    #                 resp_dict[str(ques.id)]=''
                    #                 if (val_question.qtype in ['S','SM'] and answer == val) or (assign_val and val_question.qtype == 'D' and answer == ''):
                    #                     assign_val=True
                    #                     resp_dict[str(ques.id)]=refered_keys.get('message') 
                                        
                    #                 # if (assign_val and val_question.qtype == 'D' and answer == ''):
                    #                 #     resp_dict[str(ques.id)]=refered_keys.get('message') 
                    #             # else:
                    #             #     q_id=next(iter(refered_keys))
                    #             #     answer=list(answers_list.get(str(q_id))[0].values())[0]
                    #             #     val_question=questions.get(id=q_id)
                    #             #     if (val_question.qtype == 'S' and answer == refered_keys.get(q_id)):
                    #                     # resp_dict[str(ques.id)]=refered_keys.get('message') 
                    #         else:
                    #             resp_dict[str(ques.id)]=list(answers_list.get(str(ques.id))[0].values())[0]

                    #     except:
                    #         resp_dict[str(ques.id)]=''
                        
                    
                    # elif ques.qtype in ['AP']:
                    #     # import ipdb ;ipdb.set_trace()

                    #     if user and ques.training_config.get('current_user') :
                    #         resp_dict[str(ques.id)] = user.username
                    #     else:
                    #         resp_dict[str(ques.id)]=list(answers_list.get(str(ques.id))[0].values())[0]

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
                        resp_dict[str(ques.id)]=list(answers_list.get(str(ques.id))[0].values())[0]
            except Exception as e:
                error_msg =e.args[0]
                logging.error(error_msg)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                logging.error(error_stack)
                # logger.info(f'{e} : Exception because value null for skip question. function:question_answer_dict')
    return resp_dict
# {"620":[{"T_0_0":"xgxgxy"}],"621":[{"T_0_0":"cucu"}],"622":[{"S_0_0":"1551"}],"623":[{"T_0_0":"cucu"}],"624":[{"T_0_0":"fycu"}]}

def sequence_id_creator(survey_id,resp_dict):
    try:
        with transaction.atomic():
            short_codes=[]
            if survey_id == '4':
                state_id=resp_dict['address']['1']['69']['1']
                district_id=resp_dict['address']['1']['69']['2']

                #Caching the all mastelookups 
                cache_key_lookup = INSTANCE_CACHE_PREFIX+'all_master_lookup_caching'
                master_lookup =  cache.get(cache_key_lookup)
                if not master_lookup:
                    master_lookup=list(MasterLookUp.objects.filter(active=2).values('id','name','slug'))
                    cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_lookup,master_lookup,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
                prison_ocs_id = next((sub for sub in master_lookup if str(sub['id']) == resp_dict['73']), '0')

                short_codes=State.objects.filter(id__in=[state_id]).order_by('id').values_list('short_code',flat=True)

                short_codes=list(short_codes)#[state_slug_id,district_slug_id]
                
                query="select max(substring(response->>'74',7,2)::integer) from survey_jsonanswer where survey_id = 4 and response->>'72' = {1}::text and response->>'74' like '{0}%'".format(''.join(short_codes),resp_dict['72'])
                # query="select response->>'74' from survey_jsonanswer where response->>'72' ={1}::text and response->>'74' like '{0}%' order by response->>'74' desc limit 1".format(''.join(short_codes),resp_dict['72'])
                short_codes.append(prison_ocs_id.get('slug',''))
                digit,last_idx,append_id,width='01',6,'74',2
            elif survey_id == '1':
                # import ipdb;ipdb.set_trace()
                prison_uuid=resp_dict['2']
                sub_query="select response->>'74' from survey_jsonanswer where creation_key='{0}'".format(prison_uuid)
                # query="select response->>'6' from survey_jsonanswer where response->>'6' like '{0}%' order by response->>'6' desc limit 1"             
     
                query="select max(substring(response->>'6',9,4)::integer) from survey_jsonanswer where survey_id = 1 and response->>'6' like '{0}%' "             
                append_id,digit,last_idx,width='6','0001',8,4

            with connection.cursor() as cursor:
                if survey_id == '1' :
                    cursor.execute(sub_query)
                    sub_result = cursor.fetchall()
                    short_codes.append(sub_result[0][0])
                    query=query.format(sub_result[0][0])
                
                cursor.execute(query)
                result = cursor.fetchall()

                if result:
                    idx=indexer(result[0][0],width)#[last_idx:]
                    short_codes.append(idx)
                    if int(idx) > 10 ** width - 1:
                        return resp_dict,{"2":"Unable to generate the uid for this facility(max 99 reached). Please contact administrator"}
                else:
                    short_codes.append(digit)
            resp_dict.update({append_id:''.join(short_codes)})
    except Exception as e:
        error_msg = 'Error from creating the id creation . function: sequence_id_creator \n'+e.args[0]
        logging.error(error_msg)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(error_stack)
    return resp_dict,{}

#ajax function for checking the custom validations of survey
def custom_validation_survey_wise_version1(request):
    error={}
    if request.method == 'GET':
        data = request.GET.get('ans')
        survey_id = request.GET.get('survey_id')
        json_id = request.GET.get('json_id')
        ben_uuid = request.GET.get('ben')
        json_answer=JsonAnswer.objects.filter(active=2,id=json_id)
        answers_list=json.loads(data)
        if (ben_uuid == 'None' or not ben_uuid) and (answers_list.get('2')) :
            ai_questions=answers_list.get('2')
            ben_uuid=ai_questions[0].get('S_0_0')
        questions=Question.objects.filter(active=2,block__survey_id=survey_id)
        if not request.GET.get('custom_page'):
            answers_list = question_answer_dict(questions,answers_list)
        
        # import ipdb;ipdb.set_trace()
        # if not json_answer or json_answer[0].response != answers_list:
        #     error=custom_validation_survey_wise(answers_list,int(survey_id),json_id,ben_uuid)
        # if error:
        #     error.update({'success':False})
        #     return JsonResponse(error)
        # else:
        return JsonResponse({'success':True})

def load_data_to_cache_survey_slug():
    #caching the surveys based on slug

    query2 = "SELECT jsonb_object_agg(slug, s_val) FROM ( SELECT a.slug, jsonb_build_object('id',a.id,'slug',a.slug, 'name', a.name, 'survey_type', a.survey_type, 'survey_order', a.survey_order, 'short_name', a.short_name, 'extra_config', coalesce(a.extra_config, '[]'::jsonb) ) as s_val FROM survey_survey a WHERE a.active = 2 ) as x"

    cache_key_survey_slug = INSTANCE_CACHE_PREFIX+'all_choice_surveys_slug'
    survey_cache_dict =  cache.get(cache_key_survey_slug)
    if not survey_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query2)
            result2 = cursor.fetchall()
            survey_cache_dict = json.loads(result2[0][0])
        cache_set_with_namespace(INSTANCE_CACHE_PREFIX+'FORM_BUILDER',cache_key_survey_slug,survey_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return survey_cache_dict    


def conditional_field_disable(json_response,config):
    return_data=[]
    conditional_disable=config.get('conditional_disable',{})  
    for key,value in conditional_disable.items():
        if json_response.get(key) == value:
            return_data.append(key)
    return return_data

from operator import itemgetter
@login_required(login_url='/')
def edit_survey_form(request,survey_slug,creation_key):
    from survey.api_views_version1 import add_survey_answers_version_1
    template_name = 'survey_forms/edit_answer_form.html'
    # survey=Survey.objects.get(slug=survey_slug)
    survey_dict=load_data_to_cache_survey_slug()
    survey = survey_dict.get(str(survey_slug))
    school_creation_key = request.GET.get('creation_key')
    school_name = request.GET.get('school_name')
    heading=survey.get('name')
    # caching the block based on survey id
    blocks =  load_data_to_cache_block()
    blocks = blocks.get(str(survey.get('id'))) 
    response_obj = JsonAnswer.objects.get(creation_key=creation_key)
    if survey.get('id') in [2,7]:
        disable=True
    ben=None
    if response_obj.survey.id !=10:
        ben = response_obj.response.get('237')
    ben_uuid=request.GET.get('ben',request.POST.get('ben',ben))
    skip_questions=[]
    #block for shows the beneficiary details 
    try:
        if ben_uuid:
            cached_surveys = load_data_to_cache_survey()
            benificiary=JsonAnswer.objects.get(creation_key=ben_uuid)
            json_response=benificiary.response

            profile_obj=benificiary
            ben_survey = cached_surveys.get(str(benificiary.survey_id))
            fixed_profile_ids=ben_survey.get('extra_config').get('profile_fields',[])
            # print(json_response['237'],'json_response[]')
            if not response_obj.survey.id in [2,10]:
                ans=JsonAnswer.objects.get(creation_key=json_response['237']).response
                profile_fields = question_based_answers(benificiary.survey_id,ans,fixed_profile_ids)
            if response_obj.survey.id == 10:
                profile_fields = question_based_answers(benificiary.survey_id,json_response,fixed_profile_ids)
        else:
            json_response={}
            # profile_cache_key = 'survey_heading_questions_for_'+str(benificiary.survey_id)
            # fixed_questions =  cache.get(profile_cache_key)
            # if not fixed_questions:
            #     fixed_questions = Question.objects.filter(block__survey=benificiary.survey).values('id','text','qtype','training_config').order_by('question_order')
            #     cache_set_with_namespace('FORM_BUILDER',profile_cache_key,fixed_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
        
            # preserved_prfile = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(fixed_profile_ids)])
            # profile_fields=fixed_questions.filter(id__in=fixed_profile_ids).order_by(preserved_prfile)

        #Hardcoded code for show the status of inmate 
        if ben_uuid and profile_obj.survey_id == 1 :
            # survey_heading_choices = load_data_to_cache_choices()
            # query="select response->>'574' as known_hiv,response->>'575' as new_hiv,response->>'577' as death_result,response->>'576' as tb_result,response->>'578' as sti_result,response->>'579' as syphilis_result,response->>'580' as hbv_result,response->>'581' as hbv_result,response->>'720' as death_report from survey_jsonanswer where cluster->>'BeneficiaryResponse' = '{0}' or creation_key = '{0}';".format(ben_uuid)
            # with connection.cursor() as cursor:
            #     cursor.execute(query)
            #     result = cursor.fetchall()
            #     selected_choices=[item for tuple in result for item in tuple]
            #     new_list = list(filter(lambda x: x not in ['',None],selected_choices ))
            # # status_choices=[item.get('text') for item in survey_heading_choices if str(item.get('id')) in new_list]
            # status_text=', '.join(new_list)
            try:
                status_text= ', '.join(eval(profile_obj.response.get('574','[]') or '[]'))
            except:
                status_text=profile_obj.response.get('574','')
    except Exception as e:
        error_msg =e.args[0]
        logging.error(error_msg)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(error_stack)
        json_response={}
    # added this block because in edit form loop the questions 
    survey_questions = load_data_to_cache_survey_based_questions()
    question_ids_list = list(map(itemgetter('id'), survey_questions.get(str(survey.get('id')))))

    # survey_question_key = 'survey_heading_questions_for_'+str(survey.id)
    # survey_questions =  cache.get(survey_question_key)
    # if not survey_questions:
    # survey_questions = Question.objects.filter(block__survey=survey).values('id','text','qtype','training_config').order_by('question_order')
    #     cache_set_with_namespace('FORM_BUILDER',survey_question_key,survey_questions,CACHES.get("default")['DEFAULT_SHORT_DURATION'])
  
    #Based on the skip questions hide questions inside the grid 
    if survey.get('extra_config').get('skip_question') and json_response:
        config=survey.get('extra_config').get('skip_question')
        for k,v in config.items():
            skip_questions.extend(config.get(k).get(json_response.get(k)))

    #static code for if the survey have records or not 
    if survey.get('id') == 8 and json_response:
        is_first_record=False
        first_record=JsonAnswer.objects.filter(cluster__BeneficiaryResponse=ben_uuid,survey_id=8).order_by('created').first()
        if creation_key == first_record.creation_key:
            is_first_record=True

        # gender based field for hiv form hide the question In Case of PPW inmate Linked with PPTCT
        gender_male=False
        if json_response.get('9') == '65':
            gender_male=True

    #boundaries based on user
    boundaries =  load_data_to_cache_boundaries_name()

    if not request.user.is_superuser and not request.user.is_staff:
        next_level_boundries=load_data_to_cache_boundarylevel()
        if survey.get('id') != 2 :
            boundarys=[item for item in boundaries if item.get('id') in request.session['user_parent_boundary_list']]
        else:
            boundarys=[item for item in boundaries if item.get('boundary_level_type_id') == 1]
            
    conditional_disable=conditional_field_disable(response_obj.response,survey.get('extra_config'))

    if request.method  == 'POST':
        now = datetime.now()
        date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        # response_obj = JsonAnswer.objects.get(creation_key=creation_key)
        # import ipdb;ipdb.set_trace()
        answers=json.loads(request.POST.getlist('all_in_one')[0])
        ben_uuid=request.GET.get('ben',request.POST.get('ben','0'))
        responses={
            "u_uuid": request.user.id,
            "d_uuid": "",
            "pushInput": [
                {
                "r_uuid": creation_key,
                "survey_id": str(response_obj.survey_id),
                "last_updated_date": date_time_str,
                "beneficiary_id": ben_uuid,
                "cluster_id": request.POST.get('cluster_id'),
                "answers_array":answers,
                }]
        }
        # ans=json.loads(request.POST.get('all_in_one'))
        content=add_survey_answers_version_1(request,**responses)
        logger.info('Data status updated to database:' ,json.loads(content.content.decode('utf-8')))
        result=json.loads(content.content.decode('utf-8'))
        if not result['status']:
            return render(request,template_name,locals())
        
        # add_survey_answers_version_1(request)
    
        if ben_uuid != '0':
            # profile_url=f'/configuration/profile/{survey_slug}/{ben_uuid}/'
            profile_url=f'/configuration/profile/{survey.get("slug")}/{ben_uuid}/'

        elif survey.get('id') == 2 and creation_key:
            profile_url=f'/configuration/profile/{creation_key}/'
        elif school_creation_key:
            profile_url = f'/configuration/list/{survey.get("slug")}/{school_creation_key}/{school_name}/'
        else:
            profile_url=f'/configuration/list/{survey_slug}/'
        
        # profile_url='/configuration/profile/'+survey_slug+'/'+ben_uuid+'/' if ben_uuid != '0' else '/configuration/list/'+survey_slug+'/'
        return HttpResponseRedirect(profile_url)
    return render(request,template_name,locals())



@login_required(login_url='/')
def get_boundry_based_on_parentboundry(request):
    if request.method == 'GET':
        result_set=[]
        boundry_level = request.GET.get('boundry_level', '')
        selected_boundry = request.GET.get('selected_boundry', '')

        user_id = request.GET.get('user_id', 0)
        selected_user = request.GET.get('selected_user',0)
        if selected_boundry == '0' :
            boundarys=Boundary.objects.filter(boundary_level_type_id=boundry_level,active=2).order_by('name')
            for boundary in boundarys:
                result_set.append(
                    {'id':boundary.id, 'name': boundary.name, })
        else:
            
            dj_query=Q(survey_id=1)
            #for super user 
            # if request.user.is_superuser or 3 in request.session['user_role_id']:
            dj_query.add(Q(response__address__1__234__2__in=selected_boundry),Q.AND)
            #for ppm user only
            # elif request.session['user_boundary_levelcode'] == 2 and 27 in request.session['user_role_id']:
                # dj_query.add(Q(id__in=user_facility_list),Q.AND)
                # dj_query.add(Q(response__address__1__234__2=selected_boundry),Q.AND)
            # elif request.session['user_boundary_levelcode'] == 2 and int(selected_boundry) not in request.session['user_boundary_list']:
            #     selected_boundry='0'
            #     dj_query.add(Q(response__address__1__234__2=selected_boundry),Q.AND)
            # elif request.session['user_boundary_levelcode'] == 1:
            #     dj_query.add(Q(response__address__1__234__2=selected_boundry),Q.AND)


            json_answers=JsonAnswer.objects.filter(dj_query).exclude(active=0).order_by('-modified')

            for json_data in json_answers:
                result_set.append(
                    {'value':json_data.creation_key,'id':"", 'name': json_data.response.get("231"),'facility_type':json_data.response.get("232") })
        
        return HttpResponse(json.dumps(result_set))
    


@login_required(login_url='/')
def get_location_boundry(request):
    if request.method == 'GET' :
        result_set=[]
        selected_boundry = request.GET.get('selected_boundry', '')

        #Caching the all boundaries 
        boundaries =  load_data_to_cache_boundaries_name()

        # import ipdb;ipdb.set_trace()
        # boundarys=[item for item in boundaries if str(item.get('parent')) == selected_boundry and ((request.session['user_boundary_levelcode'] == 1 and item.get('parent') in request.session['user_parent_boundary_list']) or (item.get('id') in request.session['user_boundary_list']) or (transfer_page == 'true'))]# or survey_id == '2'
        boundarys=[item for item in boundaries if str(item.get('parent')) == selected_boundry and item.get('code') in list(map(str,request.session.get('user_boundary_list',[])))]
        for boundary in boundarys:
            result_set.append({'id':boundary.get('id'), 'name': boundary.get('name'), })
        return HttpResponse(json.dumps(result_set))
    
