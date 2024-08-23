from django import template
from django.template.defaulttags import register
from django.contrib.auth.models import User
from application_master.models import *
from survey.models import *
import json,psycopg2
import logging
import sys, traceback

logger = logging.getLogger(__name__)
register = template.Library()

@register.simple_tag
def get_sql_val(i):
    results = 0
    try:
        results = eval(i.val)
    except:
        results
    return results


@register.filter
def get_item(dictionary, key):
    # print(dictionary)
    value = dictionary.get(key) if dictionary.get(key) is not None else ''
    return value

@register.filter
def index(indexable, i):
    # TODO: check if i is > lenght of indexable and return "" or error
    if indexable:
        return indexable[i]
    else:
        return ""
        
@register.simple_tag
def get_row_class(indexable,css_info, url_columns):
    try:
        row_text = ''
        col_index = css_info.get('col_index', -1)
        col_text = css_info.get('col_text','').strip().lower()
        row_css_class = css_info.get('row_class','')
        if col_index == -1:
            return ''
        else:
            row_text = indexable[col_index]
            # check if row_css column is listed in the url_columns
            # data for a url column is stored as a list of [data, url string], pick the 0 index to check if Total
            # index in url_columns starts with 1, adding 1 to col_index
            if col_index + 1 in url_columns:
                row_text = row_text[0]
            if row_text and row_text.strip().lower() == col_text:
                return row_css_class
    except:
        logger.error("exception in function set_row_class - dasboard_tags")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(
            exc_type, exc_value, exc_traceback))
        logger.error(error_stack)
        return ''

@register.simple_tag
def q_sum_list(value, start_index, end_index):
    if isinstance(value, list):
        return sum(value[start_index:end_index])
    return 0


@register.filter
def cum_sum_list(value):
    if isinstance(value, list):
        value = sum(value[5:] + value[1:2] + [value[4]])
        return value
    return 0