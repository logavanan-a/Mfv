import json

import django
import requests
import urllib3
from django import template
from django.conf import settings
from django.contrib.auth.models import User
from mis.models import MissionIndicatorAchievement

register = template.Library()

@register.simple_tag
def disply_indicator_values(res_id, ind_id, keys):
    mission_response = MissionIndicatorAchievement.objects.get(id = res_id)
    return mission_response.response.get(keys + str(ind_id))

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
