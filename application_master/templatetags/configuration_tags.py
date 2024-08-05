import json

import django
# import requests
import urllib3
from application_master.models import *
from reports.models import QuietlyReport
import base64
from dateutil.relativedelta import relativedelta
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from mis.models import MissionIndicatorAchievement, Task
from datetime import datetime

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Return the boolean of whether the user has the specified group.
    """
    return user.groups.filter(name=group_name).exists()

@register.simple_tag
def get_menu_list(request):
    """
    Return a list of menus.
    """
    group =request.user.groups.all()[0].id
    application_type_id=request.session.get('application_type_id')
    if application_type_id == 510:
        menus = Menus.objects.filter(active = 2,parent=None,group=group).exclude(id=18).order_by("menu_order")
    elif application_type_id == 511:
        menus = Menus.objects.filter(active = 2,parent=None,group=group).exclude(id=1).order_by("menu_order")
    else:
        menus = Menus.objects.filter(active = 2, parent=None,group=group).order_by("menu_order")
    return menus

# @register.simple_tag
# def get_sub_menus(request):
#     group =request.user.groups.all()[0].id
#     application_type_id=request.session.get('application_type_id')
#     if application_type_id == 510:
#         menus = Menus.objects.filter(active = 2,group=group).exclude(id=18).order_by("menu_order")
#     elif application_type_id == 511:
#         menus = Menus.objects.filter(active = 2,group=group).exclude(id=1).order_by("menu_order")
#     else:
#     return Menus.objects.filter(parent=self).order_by('menu_order')

@register.simple_tag
def disply_financial_year(start_date):
    """
    Return the financial year.
    """
    financial_year = ''
    if start_date.month in [1,2,3]:
        financial_year = f"{start_date.year-1}-{ start_date.year}"        
    else:
        financial_year =  f"{start_date.year}-{ start_date.year+1}"
    return financial_year

@register.simple_tag
def disply_indicator_values(res_id, ind_id, keys):
    """
    Return the indicator value.
    """
    mission_response = MissionIndicatorAchievement.objects.get(id = res_id)
    return mission_response.response.get(keys + str(ind_id))

@register.simple_tag
def disply_quietly_indicator_values(ind_id,pro_id=None,academic_year=None):
    """
    Return the indicator value.
    """
    try:
        quietly_report = QuietlyReport.objects.get(project = pro_id,indicator_id=ind_id,academic_year=academic_year)
    except:
        quietly_report = [{'annual_target':0,'q1_target':0,'q2_target':0,'q3_target':0,'q4_target':0,}]
    return quietly_report

@register.simple_tag
def disply_indicator_target_values(task_id, ind_id):
    """ 
    Return the mission indicator target value for program.
    """
    task_obj = Task.objects.get(active = 2, id = task_id)
    
    financial_year = ''
    if task_obj.start_date.month in [1,2,3]:
        financial_year = task_obj.start_date.year-1  
    else:
        financial_year =  task_obj.start_date.year
    try:
        mission_indicator_target = MissionIndicatorTarget.objects.get(active = 2, periodicity__range=[financial_year,financial_year], mission_indicator__id = ind_id, project = task_obj.project).target
    except:
        mission_indicator_target = ''
    return mission_indicator_target

@register.simple_tag
def disply_indicator_target_values_finance(task_id, ind_id):
    """
    Return the mission indicator target value for finance.
    """
    task_obj = Task.objects.get(active = 2, id = task_id)
    
    financial_year = ''
    if task_obj.start_date.month in [1,2,3]:
        financial_year = task_obj.start_date.year-1  
    else:
        financial_year =  task_obj.start_date.year
    try:
        mission_indicator_target = MissionIndicatorTarget.objects.get(active = 2, periodicity__range=[financial_year,financial_year], mission_indicator__id = ind_id, project = task_obj.project).approved_budget
    except:
        mission_indicator_target = ''
    return mission_indicator_target

@register.simple_tag
def disply_target_values(res_id, ind_id, keys):
    """
    Return the indicator value.
    """
    mission_response = ''

    return mission_response.response.get(keys + str(ind_id))

@register.simple_tag
def query_transform(request, **kwargs):
    """usages: {% query_transform request page=1 %}"""
    """
    Transform the query.
    """
    updated = request.GET.copy()

    for k, v in kwargs.items():
        updated[k] = v

    # trash any pjax params, we never want to render those
    try:
        del updated['page']
    except KeyError:
        pass

    return updated.urlencode()

@register.simple_tag
def get_skip_question(choice, question):
    is_skip_question = False
    if question in choice.skip_question.all():
        is_skip_question = True
    return is_skip_question

@register.filter
def integer_to_month(month):
    month_obj = datetime.strptime(str(month), '%m%Y')
    return month_obj
