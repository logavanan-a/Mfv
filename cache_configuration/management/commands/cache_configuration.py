from __future__ import unicode_literals
from django.core.management.base import BaseCommand
import psycopg2
import sys, traceback
from django.shortcuts import render
from dateutil.relativedelta import *
import datetime
import requests
import json
import calendar;
import time;
from django.core.cache import cache
from django.conf import settings


def cache_config(cachename,operation):
    cachename = settings.INSTANCE_CACHE_PREFIX + cachename
    if operation == 1:
        print('Cache Name - '+ str(cachename))
        print('Cache Value - '+ str(cache.get(cachename)))
    elif operation == 2:
        print('Cache Name - '+ str(cachename))
        print('Cache Value - '+ str(cache.get(cachename)))
        print('Deleting Cache for - '+str(cachename))
        cache.delete(cachename)
        print('Cache Deleted' )   
    elif operation == 3: 
        cachename = '__NS__'+cachename+'__NS__'
        for i in cache.get(cachename):
            print('Cache Name - '+ str(i))
            print('Cache Value - '+ str(cache.get(settings.INSTANCE_CACHE_PREFIX + i)))
    elif operation == 4:
        cachename = '__NS__'+cachename+'__NS__'
        for i in cache.get(cachename):
            print('Cache Name - '+ str(settings.INSTANCE_CACHE_PREFIX + i))
            print('Cache Value - '+ str(cache.get(settings.INSTANCE_CACHE_PREFIX + i)))
            cache.delete(settings.INSTANCE_CACHE_PREFIX + i)
            print('Cache Deleted')
        cache.delete(cachename)    
    
class Command(BaseCommand):
    import logging
    help = 'Displays current time'
    def add_arguments(self, parser):
        #Optional argument
        parser.add_argument('-n', '--cache', type=str,nargs='+' )
        parser.add_argument('-o', '--operator', type=int)
        # parser.add_argument('-v', '--verbosity', type=list, help='Indicates the year for which to pull data.For the selected component' )
    
    def handle(self, *args, **kwargs):
        # kwargs['verbosity'] = int(kwargs['verbosity'])
        # if kwargs['verbosity'] > 1:
        operator = kwargs.get('operator')
        cache = kwargs.get('cache')
        if operator is None or len(cache)< 1:
            print('Cache name and operator(1- details,2- delete) is mandatory')
        else:
            cache_config(cache[0],operator)
    
#operation 1 = shows all values in the namespace key
# operation 2 = delete the namesapce key
# operation 3 = shows all the values inside each cache key in a namespace
# operation 4 = deletes all the values fro each key inside a namespace    