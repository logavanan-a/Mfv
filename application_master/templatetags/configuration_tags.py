import json

import django
import requests
import urllib3
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from mis.models import MissionIndicatorAchievement, Task
from application_master.models import *

register = template.Library()


@register.simple_tag
def get_usermenu_list(request):
    # role_ids = request.session.get('role_id',None)
    menus = []
    if True:
        # user_role ,created= UserRoles.objects.get_or_create(user = user)
        # role_ids = user_role.role_type_id
        # role_configs = RoleConfig.objects.filter(role__id = role_ids,
        #                 view = True)
        # menu_ids = list(set(role_configs.values_list('menu__id', flat = True)))
        menus = Menus.objects.filter(active = 2).order_by("menu_order")
    return menus



@register.simple_tag
def disply_indicator_values(res_id, ind_id, keys):
    mission_response = MissionIndicatorAchievement.objects.get(id = res_id)
    return mission_response.response.get(keys + str(ind_id))

from dateutil.relativedelta import relativedelta
@register.simple_tag
def disply_indicator_target_values(task_id, ind_id):
    task_obj = Task.objects.get(id = task_id)
    start_date = task_obj.start_date
    end_date = start_date+relativedelta(months=12)

    try:
        mission_indicator_target = MissionIndicatorTarget.objects.get(periodicity_date__range=[start_date, end_date ], mission_indicator__id = ind_id, project__id = task_obj.project.id).target
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
