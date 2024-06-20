# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.cache import cache
from django.shortcuts import render
from django.conf import settings
from survey.models import Survey
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
