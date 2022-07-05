from django import template
import django
import requests
from django.conf import settings

from django.contrib.auth.models import User
import json
import urllib3

register = template.Library()

@register.simple_tag
def get_mission_indicator_list(request):
    menus = []
  
    return menus