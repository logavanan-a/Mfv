from django import template
import django
import requests
from django.conf import settings

from django.contrib.auth.models import User
import json
import urllib3

from mis.models import MissionResponse
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def disply_indicator_values(res_id, ind_id, keys):
    mission_response = MissionResponse.objects.get(id = res_id)

    return mission_response.response.get(keys + str(ind_id))