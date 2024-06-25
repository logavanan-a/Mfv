# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.cache import cache
from django.shortcuts import render
from django.conf import settings
from survey.models import Survey
from django.db import connection,transaction
import json
# Create your views here.




# common function for Setting Cache
def cache_set_with_namespace(namespace, key, value,cache_time = None):
     key = settings.INSTANCE_CACHE_PREFIX + key
     namespace_key = "__NS__"+settings.INSTANCE_CACHE_PREFIX+namespace+"__NS__"
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

#common function for Deleting Cahce
def cache_delete_namespace(namespace):
    namespace_key = "__NS__"+settings.INSTANCE_CACHE_PREFIX+namespace+"__NS__"
    cache_list = cache.get(namespace_key)
    if cache_list:
        for i in cache_list:
            cache.delete(str(i))
    cache.set(namespace_key, [])

# usage: 
# cache_delete_namespace("LandingPageRollup")


########## cache data #########

def load_data_to_cache_survey_objects():
   # caching the surveys
   cache_key_survey = 'all_surveys_objects'
   surveys = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key_survey)
   if not surveys:
      surveys = {s.id:s for s in Survey.objects.filter(active=2).order_by('survey_order')}
      cache_set_with_namespace('FORM_BUILDER', cache_key_survey, surveys,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
   return surveys

def load_data_to_cache_survey_based_questions():
    # caching the questions based on the survey
    query = "SELECT jsonb_object_agg(survey_id, question_info) FROM ( SELECT sb.survey_id, jsonb_agg( jsonb_build_object( 'id', a.id, 'qtype', a.qtype, 'text', a.text, 'is_grid', a.is_grid, 'mandatory', a.mandatory, 'api_json', a.api_json, 'is_editable', a.is_editable, 'api_qtype', a.api_qtype, 'parent', a.parent_id, 'training_config', a.training_config,'display_has_name', a.display_has_name,'question_filter',a.question_filter,'address_question',a.address_question,'deactivated_date',a.deactivated_date,'active',a.active ) ORDER BY a.question_order ) AS question_info FROM survey_question a inner join survey_block sb on sb.id = a.block_id WHERE a.active = 2 AND a.parent_id IS NULL GROUP BY sb.survey_id ) AS x"

    cache_key_questions = 'survey_based_questions'
    survey_questions = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key_questions)
    if not survey_questions:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            survey_questions = json.loads(result[0][0] or '{}')
        cache_set_with_namespace('FORM_BUILDER', cache_key_questions, survey_questions,
                                 settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return survey_questions


def load_data_to_cache_question_validation():
    #caching the question validation for forms
    query = "select jsonb_object_agg(question_id, q_val) from (select a.question_id, jsonb_build_object('id',a.id, 'validation_type',b.validation_type, 'code',b.code, 'max_value',a.max_value,'min_value',a.min_value,'message',a.message,'mandatory',c.mandatory) as q_val from survey_questionvalidation a inner join survey_validations b on a.validationtype_id = b.id inner join survey_question c on c.id =a.question_id where a.active = 2 ) as x"

    cache_key_survey_display = 'all_question_validation_cache'
    validation_cache_dict = cache.get(settings.INSTANCE_CACHE_PREFIX + cache_key_survey_display)
    if not validation_cache_dict:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            validation_cache_dict = json.loads(result[0][0])
        cache_set_with_namespace('FORM_BUILDER',cache_key_survey_display,validation_cache_dict,settings.CACHES.get("default")['DEFAULT_SHORT_DURATION'])
    return validation_cache_dict
