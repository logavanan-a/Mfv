from __future__ import unicode_literals

import json

import requests
from application_master.models import (BaseContent, Mission, MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionQuestion)
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth
from django.contrib.sessions.models import Session
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)

from mis.models import MissionIndicatorTarget, MissionResponse


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

        MissionResponse.objects.create(created_by = request.user, mission = mission_obj , response = results)
        if True:
            return redirect('/mission/list/')

    return render(request, 'mis/indicator_list.html', locals())

@login_required(login_url='/login/')
def mission_indicator_edit(request):
    mission_respons_obj = MissionResponse.objects.all()
    return render(request, 'mis/mission_indicator_edit.html', locals())

@login_required(login_url='/login/')
def missionindicator_table_edit(request, ids, id):
    mission_obj = Mission.objects.get(id = ids)
    heading = mission_obj.name
    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = ids)
    mission_respose_obj = MissionResponse.objects.get(id = id)

    if request.method == 'POST':
        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])
        
        mission_respose_obj = MissionResponse.objects.get(id = id)
        mission_respose_obj.response = results
        mission_respose_obj.save()

        if True:
            return redirect('/mission/list/')
    return render(request, 'mis/indicator_edit.html', locals())

@login_required(login_url='/login/')
def generator_form(request, id):
    mission_obj = Mission.objects.get(id = id)
    heading = mission_obj.name
    missionform_obj = MissionQuestion.objects.filter(mission__id = id)

    if request.method == 'POST':
        data = request.POST
        # print(data,'data')
        # files = request.FILES.get('')
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = values[0]

        MissionResponse.objects.create(created_by = request.user, mission = mission_obj, response = results)

        if True:
            return redirect('/mission_form/list/')

    return render(request, 'mis/generator_form.html', locals())

# def mission_add(request):
#     mi_obj = MissionIndicator.objects.all()
#     data = request.POST
#     result = []
#     for mi in mi_obj:
#         mission_add = data.getlist('pro_'+str(mi.id))
#         result.append(mission_add)
#     return render(request, 'mis/add_child_form.html', locals())

def missionindicator_target(request, id):
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
        MissionIndicatorTarget.objects.create(created_by = request.user, mission = mission_obj, response = results)

        if True:
            return redirect('/mission/list/')

    return render(request, 'mis/add_target.html', locals())

@login_required(login_url='/login/')
def mission_target_edit(request):
    mission_respons_obj = MissionIndicatorTarget.objects.all()
    return render(request, 'mis/mission_target_edit.html', locals())


@login_required(login_url='/login/')
def missiontarget_table_edit(request, ids, id):
    mission_obj = Mission.objects.get(id = ids)
    heading = mission_obj.name
    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = ids)
    mission_target_obj = MissionIndicatorTarget.objects.get(id = id)

    if request.method == 'POST':
        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])
        
        mission_respose_obj = MissionIndicatorTarget.objects.get(id = id)
        mission_respose_obj.response = results
        mission_respose_obj.save()

        if True:
            return redirect('/mission/list/')
    return render(request, 'mis/target_edit.html', locals())
