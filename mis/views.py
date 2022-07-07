from __future__ import unicode_literals

import json

import requests
from application_master.models import (BaseContent, Mission, MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionQuestion, VisionCentre)
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth
from django.contrib.sessions.models import Session
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)
from django.views.generic import RedirectView, View

from mis.models import MissionIndicatorAchievement, MissionIndicatorTarget, Task


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
        print(user)
        if user is not None:
            login(request, user)
            # configure_error = load_user_details_to_sessions(request)
            # if not configure_error:
            return redirect('/mission-list/')
            # return redirect('/task-list/')
            # else:
            #     logout(request)
        else:
            error_message = "Invalid Username and Password"
    return render(request, 'login.html', locals())

class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    url = '/login/'
    def get(self, request, *args, **kwargs):
        logout(request)
        request.session['partner_key']=''
        return super(LogoutView, self).get(request, *args, **kwargs)

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
def missionindicator_table(request, slug):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    mic_obj = MissionIndicatorCategory.objects.filter(mission__slug = slug)

    if request.method == 'POST':
        data = request.POST
        # print(data,'data')
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])

        MissionIndicatorAchievement.objects.create(created_by = request.user, mission = mission_obj , response = results)
        if True:
            return redirect('/mission-list/')

    return render(request, 'mis/indicator_list.html', locals())

@login_required(login_url='/login/')
def mission_indicator_edit(request):
    mission_respons_obj = MissionIndicatorAchievement.objects.all()
    return render(request, 'mis/mission_indicator_edit.html', locals())

@login_required(login_url='/login/')
def missionindicator_table_edit(request, ids, id):
    mission_obj = Mission.objects.get(id = ids)
    heading = mission_obj.name
    mic_obj = MissionIndicatorCategory.objects.filter(mission__id = ids)
    mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)

    if request.method == 'POST':
        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])
        
        mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
        mission_respose_obj.response = results
        mission_respose_obj.save()

        if True:
            return redirect('/mission-list/')
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

        MissionIndicatorAchievement.objects.create(created_by = request.user, mission = mission_obj, response = results)

        if True:
            return redirect('/mission_form/list/')

    return render(request, 'mis/generator_form.html', locals())

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
            return redirect('/mission-list/')

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
            return redirect('/mission-list/')
    return render(request, 'mis/target_edit.html', locals())


def task_list(request):
    task_obj = Task.objects.filter(user = request.user)

    return render(request, 'mis/task_list.html', locals())


# Task create scripts
# def task_create():
#     for user_obj in User.objects.filter(is_superuser = False):
#         if user_obj:
#             for visio_ncentre in VisionCentre.objects.all():
#                 string_cancate = visio_ncentre.mission.name +" "+visio_ncentre.name+" july 2022"
#                 print(string_cancate)
#                 Task.objects.create(name = string_cancate,user = user_obj, vision_centre = visio_ncentre,
#                 start_date = "2022-07-01",end_date = "2022-07-31"
#                 )
