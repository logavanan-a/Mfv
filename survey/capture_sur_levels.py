from datetime import datetime
from survey.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
import os
import pytz


def pagination(request, plist):
    paginator = Paginator(plist, 1)
    page = request.GET.get('page', '')
    try:
        plist = paginator.page(page)
    except PageNotAnInteger:
        plist = paginator.page(1)
    except EmptyPage:
        plist = paginator.page(paginator.num_pages)
    return plist

def convert_string_to_date(string):
    date_object = ''
    try:
        date_object = datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    except:
        date_object = None
    if not date_object:
        try:
            date_obj = datetime.strptime(string, '%Y-%m-%d %H:%M:%S.%f')
            date_object = datetime(int(date_obj.year),int(date_obj.month),int(date_obj.day),int(date_obj.hour),int(date_obj.minute),int(date_obj.second),int(date_obj.microsecond),pytz.UTC)
        except:
            date_object = None
    return date_object

def convert_date_to_string(string):
    date_object = None
    try:
        date_object = string.strftime('%Y-%m-%d %H:%M:%S.%f')
    except:
        date_object = None
    return date_object