import json

import requests
from application_master.models import *

#(BaseContent, District,Mission, MissionIndicator, MissionIndicatorCategory, PartnerMissionMapping, UserPartnerMapping)

from django.conf import settings
from django.contrib.auth import authenticate, get_user, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth
from django.contrib.sessions.models import Session
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView, View

from mis.models import MissionIndicatorAchievement, Task

pg_size = 10
def get_pagination(request, users):
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
    user = get_user(request)
    user_role = str(user.groups.last())

    if request.method == 'POST':
        data = request.POST
        working_day = request.POST.get('working_day')
        project_reference_file = request.FILES['project_reference_file']

        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken' and key != 'working_day' and values[0] != '':
                results[key] = int(values[0])
                
        mission_add = MissionIndicatorAchievement.objects.create(task = task_obj , response = results)

        if working_day:
            mission_add.number_working_days = working_day

        if project_reference_file:
            mission_add.project_reference_file = project_reference_file  

        mission_add.save()

        return redirect('mis:mission_edit', slug = slug, task_id = task_id, id = mission_add.id,)
        # return redirect('/task-list/')

    return render(request, 'mis/indicator_list.html', locals())

# @login_required(login_url='/login/')
# def mission_indicator_edit(request):
#     mission_indicator_achievement = MissionIndicatorAchievement.objects.all()
#     return render(request, 'mis/mission_indicator_edit.html', locals())

@login_required(login_url='/login/')
def missionindicator_edit(request, slug, id,task_id):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2')
    user = get_user(request)
    user_role = str(user.groups.last())
    task_obj = Task.objects.get(id = task_id)

    if request.method == 'POST':

        working_day = request.POST.get('working_day')
        project_reference_file = request.FILES['project_reference_file']

        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken' and values[0] != '':
                results[key] = int(values[0])
        mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
        mission_respose_obj.response = results

        if working_day:
            mission_respose_obj.number_working_days = working_day

        if project_reference_file:
            mission_respose_obj.project_reference_file = project_reference_file 

        mission_respose_obj.save()

        return redirect('/task-list/')
    return render(request, 'mis/indicator_edit.html', locals())

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
        
        return redirect('/mission-list/')

    return render(request, 'mis/target_edit.html', locals())

@login_required(login_url='/login/')
def task_list(request):
    heading= 'Task List'
    user = get_user(request)
    
    if user.groups.filter(name = 'Partner Admin').exists():
        user_lists = UserPartnerMapping.objects.get(user = request.user)
        for user_list in UserPartnerMapping.objects.filter(partner = user_lists.partner).exclude(user = request.user):
            task_obj = Task.objects.filter(user = user_list.user)
            # print(task_obj,obj_list)
    else:
        task_obj = Task.objects.filter(user = request.user)

    object_list = get_pagination(request, task_obj)
    return render(request, 'mis/task_list.html', locals())


@csrf_exempt 
def task_status_changes(request, task_id):
    if request.method == "POST":
        status_val = request.POST.get('status_val')
        print(status_val,'status_val')
        task_obj = Task.objects.get(id = task_id)
        task_obj.task_status = status_val
        task_obj.save()
        return HttpResponse({"message":'true'} , content_type="application/json")
    return HttpResponse({"message":'false'}, content_type="application/json")  

def project_list(request):
    heading= 'Project List'

    partner = UserPartnerMapping.objects.get(user = request.user).partner
    partner_mission_mapping_ids = PartnerMissionMapping.objects.filter(partner = partner).values_list('id', flat=True)
    project_obj = Project.objects.filter(partner_mission_mapping__id__in = partner_mission_mapping_ids, partner_mission_mapping__mission__id = 2 )

    # project_obj = Project.objects.all()
    object_list = get_pagination(request, project_obj)
    return render(request, 'project/project_list.html', locals())

class ProjectAdd(View):
    template_name = 'project/project_add_edit.html'

    def get(self, request):
        heading= 'Project Add'
        districts = District.objects.all()
        return render(request,self.template_name,locals())

    def post(self, request):
        data = request.POST
        name = data.get('name')
        district = data.get('district')
        location = data.get('location')
        district_obj = District.objects.get(id = district)

        partner = UserPartnerMapping.objects.get(user = request.user).partner
        partner_mission_mapping_obj = PartnerMissionMapping.objects.get(partner = partner,mission__id = 2)
        project_add = Project.objects.create(name = name, partner_mission_mapping = partner_mission_mapping_obj, district = district_obj, location=location )
        
        return redirect('/project-list/')
        # return render(request,'project/project_list.html', locals())

class ProjectUpdate(View):
    template_name = 'project/project_add_edit.html'

    def get(self, request, id):
        heading= 'Project Edit'
        districts = District.objects.all()
        project_obj = Project.objects.get(id = id)
        return render(request,self.template_name,locals())

    def post(self, request, id):
        data = request.POST
        name = data.get('name')
        district = data.get('district')
        location = data.get('location')
                
        district_obj = District.objects.get(id = district)
        project_update = Project.objects.get(id = id)
        project_update.name = name
        project_update.district = district_obj
        project_update.location = location
        project_update.save()
                
        return redirect('/project-list/')
        # return render(request, self.template_name, locals())