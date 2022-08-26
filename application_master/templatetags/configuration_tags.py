import json

import django
import requests
import urllib3
from application_master.models import *
import base64
from dateutil.relativedelta import relativedelta
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from mis.models import MissionIndicatorAchievement, Task

register = template.Library()


@register.simple_tag
def get_menu_list(request):
    # role_ids = request.session.get('role_id',None)
    return Menus.objects.filter(active = 2, parent=None).order_by("menu_order")

@register.simple_tag
def disply_financial_year(start_date):

    financial_year = ''
    if start_date.month in [1,2,3]:
        financial_year = f"{start_date.year-1}-{ start_date.year}"        
    else:
        financial_year =  f"{start_date.year}-{ start_date.year+1}"
    return financial_year

@register.simple_tag
def disply_indicator_values(res_id, ind_id, keys):
    mission_response = MissionIndicatorAchievement.objects.get(id = res_id)
    return mission_response.response.get(keys + str(ind_id))

@register.simple_tag
def disply_indicator_target_values(task_id, ind_id):
    task_obj = Task.objects.get(id = task_id)

    financial_year = ''
    if task_obj.start_date.month in [1,2,3]:
        financial_year = f"{task_obj.start_date.year-1}"        
    else:
        financial_year =  f"{task_obj.start_date.year}"
    
    # print(financial_year,'financial_year', task_obj.start_date)

    try:
        mission_indicator_target = MissionIndicatorTarget.objects.get(periodicity_date__year=financial_year, mission_indicator__id = ind_id, project__id = task_obj.project.id).target
    except:
        mission_indicator_target = ''
    return mission_indicator_target

@register.simple_tag
def disply_target_values(res_id, ind_id, keys):
    mission_response = ''

    return mission_response.response.get(keys + str(ind_id))

@register.simple_tag
def query_transform(request, **kwargs):
    """usages: {% query_transform request page=1 %}"""
    updated = request.GET.copy()

    for k, v in kwargs.items():
        updated[k] = v

    # trash any pjax params, we never want to render those
    try:
        del updated['page']
    except KeyError:
        pass

    return updated.urlencode()

# from base64 import b64decode
# @register.simple_tag
# def id_to_hash_code(mission, id):
#     sample_string = mission+''+str(id)
#     hash_code = base64.b64encode(sample_string.encode()).decode("ascii").replace('=','9')
#     return hash_code