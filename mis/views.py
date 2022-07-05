from __future__ import unicode_literals

import csv
import json
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# from child_management.models import *
from django.contrib.auth.models import User, auth
# from child_management.views import *     
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Subquery
# from master_data.models import *
from django.http import HttpResponseRedirect, JsonResponse
# from schedule import every, repeat, run_pending
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)
# from django.db import connection
from django.utils.encoding import smart_str

from .models import *
from application_master.models import *


def login_view(request):
    heading = "Login"
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            findUser = User._default_manager.get(username__iexact=username)
        except User.DoesNotExist:
            findUser = None
        if findUser is not None:
            username = findUser.get_username()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # configure_error = load_user_details_to_sessions(request)
            # if not configure_error:
            return redirect('/mission/list/')
            # else:
            #     logout(request)
        else:
            error_message = "Invalid Username and Password"
    return render(request, 'login.html', locals())

@login_required(login_url='/login/')
def mission_list(request):
    heading = "Mission List" 
    mission_obj = Mission.objects.filter(mission_template = '1')

    return render(request, 'mis/mission_list.html', locals())

@login_required(login_url='/login/')
def mission_form_list(request):
    heading = "Mission Form List" 

    mission_obj = Mission.objects.filter(mission_template = '2')

    return render(request, 'mis/missionform_list.html', locals())

@login_required(login_url='/login/')
def missionindicator_table(request, id):
    mission_obj = Mission.objects.get(id = id)
    heading = mission_obj.name

    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = id)

    if request.method == 'POST':
        data = request.POST
        # print(data,'data')

        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])

        print(results,'data')

        MissionResponse.objects.create(created_by = request.user, mission = mission_obj , response = results)




        
        if True:
            return redirect('/mission/list/')

    return render(request, 'mis/indicator_list.html', locals())


def missionindicator_table_edit(request, ids, id):
    mission_obj = Mission.objects.get(id = ids)
    heading = mission_obj.name

    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = ids)

    mission_respose_obj = MissionResponse.objects.get(id = id)

    if request.method == 'POST':
        data = request.POST
        # print(data,'data')

        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])

        print(results,'data')




    return render(request, 'mis/indicator_edit.html', locals())



@login_required(login_url='/login/')
def generator_form(request, id):
    mission_obj = Mission.objects.get(id = id)
    heading = mission_obj.name

    missionform_obj = MissionQuestion.objects.filter(mission__id = id)

    if request.method == 'POST':
        data = request.POST
        print(data,'data')
        files = request.FILES.get('')
        print(data,'data')

        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = values[0]

        MissionResponse.objects.create(created_by = request.user, mission = mission_obj , response = results)

        # survey = MissionQuestion.objects.get(id=int(survey_ids))
        # questions = Question.objects.filter(block__survey=survey,active=2)

        if True:
            return redirect('/mission_form/list/')

    return render(request, 'mis/generator_form.html', locals())

def mission_add(request):
    mi_obj = MissionIndicator.objects.all()
    data = request.POST
    result = []
    for temp in mi_obj:
            one = data.getlist('pro_'+str(temp.id))
            result.append(one)

    print(result)

    return render(request, 'mis/add_child_form.html', locals())

def mission_indicator_edit(request):

    mission_respons_obj = MissionResponse.objects.all()

    return render(request, 'mis/mission_indicator_edit.html', locals())
