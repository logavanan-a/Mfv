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

from mis.models import (MissionIndicatorAchievement,
                        Task)
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


pg_size = 10
def get_pagination(request,users):
    paginator = Paginator(users, pg_size) # Show no of object per page
    page = request.GET.get('page',1)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    return users

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
            return redirect('/task-list/')
            # configure_error = load_user_details_to_sessions(request)
            # if not configure_error:
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
    url = '/'
    def get(self, request, *args, **kwargs):
        logout(request)
        request.session['partner_key']=''
        return super(LogoutView, self).get(request, *args, **kwargs)

@login_required(login_url='/login/')
def mission_list(request):
    heading = "Mission Indicator List" 
    mission_obj = Mission.objects.filter(mission_template = '1')
    return render(request, 'mis/mission_list.html', locals())

@login_required(login_url='/login/')
def mission_form_list(request):
    heading = "Mission Form List" 
    mission_obj = Mission.objects.filter(mission_template = '2')
    return render(request, 'mis/missionform_list.html', locals())

@login_required(login_url='/login/')
def missionindicator_add(request, slug,task_id):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2')
    task_obj = Task.objects.get(id = task_id)

    if request.method == 'POST':
        data = request.POST
        # print(data,'data')
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = int(values[0])

        MissionIndicatorAchievement.objects.create(task = task_obj , response = results)
        
        return redirect('/task-list/')

    return render(request, 'mis/indicator_list.html', locals())

@login_required(login_url='/login/')
def mission_indicator_edit(request):
    mission_indicator_achievement = MissionIndicatorAchievement.objects.all()
    return render(request, 'mis/mission_indicator_edit.html', locals())

@login_required(login_url='/login/')
def missionindicator_table_edit(request, slug, id):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    # mic_obj = MissionIndicatorCategory.objects.filter(mission__slug = slug)

    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2')

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
        return redirect('/task-list/')

    return render(request, 'mis/indicator_edit.html', locals())

@login_required(login_url='/login/')
def generator_form(request, id):
    mission_obj = Mission.objects.get(id = id)
    heading = mission_obj.name
    missionform_obj = MissionQuestion.objects.filter(mission__id = id)

    if request.method == 'POST':
        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken':
                results[key] = values[0]
        MissionIndicatorAchievement.objects.create( response = results)
      
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

@login_required(login_url='/login/')
def task_list(request):
    heading = " Task List" 
    task_obj = Task.objects.filter(user = request.user)

    object_list = get_pagination(request, task_obj)
    return render(request, 'mis/task_list.html', locals())