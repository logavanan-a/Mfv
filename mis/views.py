import json
from datetime import datetime

import requests
from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget, Partner,
                                       PartnerMissionMapping, Project,
                                       ProjectDonorMapping, ProjectFiles,
                                       State, UserPartnerMapping)
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import authenticate, get_user, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User, auth
from django.contrib.sessions.models import Session
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import (HttpResponse, HttpResponseRedirect, redirect,
                              render)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView, View
from mis.models import MissionIndicatorAchievement, Task, DataEntryRemark


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
            try:
                user_partner = UserPartnerMapping.objects.get(user = user)
                partner_mission_mapping_id = PartnerMissionMapping.objects.filter(mission__id__in= [1,2],partner=user_partner.partner).values_list('id', flat = True)
                request.session['user_partner'] = user_partner.partner.name
                request.session['partner_mission_mapping_id'] = list(partner_mission_mapping_id)
            except:
                user_partner = ''              
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


@login_required(login_url='/')
def missionindicator_add(request, slug,task_id):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    task_obj = Task.objects.get(id = task_id)
    user = get_user(request)
    user_role = str(user.groups.last())

    if request.method == 'POST':
        data = request.POST
        working_day = request.POST.get('working_day')
        camp_organized = request.POST.get('camp_organized')
        project_reference_file = request.FILES.get('project_reference_file')

        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken' and key != 'working_day' and key != 'camp_organized' and values[0] != '':
                results[key] = values[0]

        mission_add = MissionIndicatorAchievement.objects.create(task = task_obj , response = results)

        if working_day:
            mission_add.number_working_days = working_day
            
        if camp_organized:
            mission_add.camp_organized = camp_organized

        if project_reference_file:
            mission_add.project_reference_file = project_reference_file  

        mission_add.save()

        return redirect('mis:mission_edit', slug = slug, task_id = task_id, id = mission_add.id,)
        # return redirect('/task-list/')

    return render(request, 'mis/indicator_list.html', locals())

@login_required(login_url='/')
def missionindicator_edit(request, slug, id,task_id):
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    user = get_user(request)
    user_role = str(user.groups.last())

    dataentry_obj = DataEntryRemark.objects.filter(task__id=task_id).order_by('-id')
    if request.method == 'POST':
        working_day = request.POST.get('working_day')
        camp_organized = request.POST.get('camp_organized')
        project_reference_file = request.FILES.get('project_reference_file')
        data = request.POST
        temp = dict(data)
        results = {}
        for key,values in temp.items():
            if key != 'csrfmiddlewaretoken' and key != 'working_day' and key != 'camp_organized' and values[0] != '':
                results[key] = values[0]
        mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
        mission_respose_obj.response = results

        if working_day:
            mission_respose_obj.number_working_days = working_day
        
        if camp_organized:
            mission_respose_obj.camp_organized = camp_organized

        if project_reference_file:
            mission_respose_obj.project_reference_file = project_reference_file 
        mission_respose_obj.save()

        return redirect('/task-list/')
    return render(request, 'mis/indicator_edit.html', locals())

@login_required(login_url='/')
def task_list(request):
    heading= 'Task List'
    user = get_user(request)

    previous_month = datetime.now() - relativedelta(months=1)
    below_last_two_month = datetime.now().date() - relativedelta(months=2)

    mission_objs = Mission.objects.all()
    project_objs = Project.objects.filter(active=2).order_by('name')

    filter_data = request.GET
    mission = filter_data.get('mission') if(filter_data.get('mission') != 'None') else None
    project = filter_data.get('project') if(filter_data.get('project') != 'None') else None
    month = filter_data.get('month') if(filter_data.get('month') != 'None') else None
    year = filter_data.get('year') if(filter_data.get('year') != 'None') else None
    month_year = filter_data.get('month_year') if(filter_data.get('month_year') != 'None') else None
    archive = filter_data.get('archive') if(filter_data.get('archive') != 'None') else None

    if(archive != None or month != None or year != None or project != None or mission != None):
        task_obj = Task.objects.filter(start_date__month__lte = below_last_two_month.month, start_date__year__lte = below_last_two_month.year).order_by('listing_order')
    else:
        task_obj = Task.objects.filter(start_date__month = previous_month.month, start_date__year = previous_month.year).order_by('listing_order')

    if mission:
        project_objs = project_objs.filter(partner_mission_mapping__mission__id = mission)
        task_obj = task_obj.filter(project__partner_mission_mapping__mission__id = mission)

    if project:
        task_obj = task_obj.filter(project__id = project)

    if year:
        task_obj = task_obj.filter(start_date__year = year)
    
    if month:
        task_obj = task_obj.filter(start_date__month = month)

    if month_year != 'None' and month_year:
        month_year_list = month_year.split('-')
        task_obj = Task.objects.filter(start_date__year = month_year_list[0]).filter(start_date__month = month_year_list[1])

    if user.groups.filter(name = 'Partner Admin').exists():
        user_lists = UserPartnerMapping.objects.get(user = request.user)
        for partner_list in UserPartnerMapping.objects.filter(partner = user_lists.partner):
            task_obj = task_obj.filter(project__partner_mission_mapping__partner = partner_list.partner).order_by('listing_order')
    
    elif user.groups.filter(name = 'Project In-charge').exists():
        task_obj = task_obj.filter(project_in_charge = request.user).order_by('listing_order')
    
    else:
        user_lists = UserPartnerMapping.objects.get(user = request.user)
        for partner_list in UserPartnerMapping.objects.filter(partner = user_lists.partner):
            task_obj = task_obj.filter(user = request.user, project__partner_mission_mapping__partner = partner_list.partner).order_by('listing_order')
        # task_obj = task_obj.filter(user = request.user,start_date__month__lte = below_last_two_month.month, start_date__year__lte = below_last_two_month.year).order_by('listing_order')
    
    object_list = get_pagination(request, task_obj)
    page_number_display_count = 5
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + page_number_display_count if page_number_start + \
        page_number_display_count < object_list.paginator.num_pages else object_list.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'mis/task_list.html', locals())

@csrf_exempt 
def task_status_changes(request, task_id):
    if request.method == "POST":
        status_val = request.POST.get('status_val')
        remark =request.POST.get('remark')
        task_obj = Task.objects.get(id = task_id)
        task_obj.task_status = status_val
        task_obj.save()
        if status_val in ['1', '2']:
            DataEntryRemark.objects.create(task = task_obj, remark = remark, user_name = request.user)
        return HttpResponse({"message":'true'} , content_type="application/json")
    return HttpResponse({"message":'false'}, content_type="application/json")  

@login_required(login_url='/')
def project_list(request):
    heading= 'Project List'
    partner = UserPartnerMapping.objects.get(user = request.user).partner
    partner_mission_mapping_ids = PartnerMissionMapping.objects.filter(partner = partner).values_list('id', flat=True)
    project_obj = Project.objects.filter(partner_mission_mapping__id__in = partner_mission_mapping_ids, partner_mission_mapping__mission__id__in = [2,1])
    object_list = get_pagination(request, project_obj)

    page_number_display_count = 5
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + page_number_display_count if page_number_start + \
        page_number_display_count < object_list.paginator.num_pages else object_list.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'project/project_list.html', locals())

def get_district(request, state_id):
    if request.method == 'GET' and request.is_ajax():
        result_set = []
        fossilahsessions = District.objects.filter(state__id=state_id)
        for fossilahsession in fossilahsessions:
            result_set.append(
                {'id': fossilahsession.id, 'name': fossilahsession.name,})
        return HttpResponse(json.dumps(result_set))

class ProjectAdd(View):
    template_name = 'project/project_add_edit.html'

    @method_decorator(login_required(login_url='/'))
    def get(self, request):
        heading= 'Project Add'
        states = State.objects.all()
        # districts = District.objects.all()
        mission_obj = PartnerMissionMapping.objects.filter(id__in = request.session['partner_mission_mapping_id'])
        return render(request,self.template_name,locals())

    @method_decorator(login_required(login_url='/'))
    def post(self, request):
        data = request.POST
        name = data.get('name')
        district = data.get('district')
        location = data.get('location')
        start_date = data.get('start_date')
        district_obj = District.objects.get(id = district)
        partner_mission_mapping_id = data.get('partner_mission_mapping')
        if partner_mission_mapping_id:
            partner = UserPartnerMapping.objects.get(user = request.user).partner
            partner_mission_mapping_obj = PartnerMissionMapping.objects.get(partner = partner, id = partner_mission_mapping_id)
        project_add = Project.objects.create(name = name, start_date = start_date, partner_mission_mapping = partner_mission_mapping_obj, district = district_obj, location=location )
        return redirect('/project-list/')
        # return render(request,'project/project_list.html', locals())


class ProjectUpdate(View):
    template_name = 'project/project_add_edit.html'
    
    @method_decorator(login_required(login_url='/'))
    def get(self, request, id):
        heading= 'Project Edit'
        states = State.objects.all()
        mission_obj = PartnerMissionMapping.objects.filter(id__in = request.session['partner_mission_mapping_id'])
        project_obj = Project.objects.get(id = id)
        districts = District.objects.filter(id = project_obj.district.id)
        return render(request,self.template_name,locals())

    @method_decorator(login_required(login_url='/'))
    def post(self, request, id):
        data = request.POST
        name = data.get('name')
        district = data.get('district')
        location = data.get('location')
        start_date = data.get('start_date')
        district_obj = District.objects.get(id = district)
        
        # partner_mission_mapping_id = data.get('partner_mission_mapping')
        # if partner_mission_mapping_id:
            # partner = UserPartnerMapping.objects.get(user = request.user).partner
            # partner_mission_mapping_obj = PartnerMissionMapping.objects.get(partner = partner, id = partner_mission_mapping_id)
        
        project_update = Project.objects.get(id = id)
        project_update.name = name
        project_update.start_date = start_date
        project_update.district = district_obj
        project_update.location = location
        project_update.save()
                
        return redirect('/project-list/')
        # return render(request, self.template_name, locals())

@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def user_listing(request):
    heading = "User Management"
    # all_fields = User._meta.fields[4:-1]
    user_role_location_config = UserPartnerMapping.objects.filter(
        active=2)
    groups = Group.objects.all().exclude(id=11)

    object_list = get_pagination(request, user_role_location_config)
    # page_number_display_count = PAGE_NUMBER_DISPLAY_COUNT
    # current_page = request.GET.get('page', 1)
    # page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    # page_number_end = page_number_start + page_number_display_count if page_number_start + \
    #     page_number_display_count < data.paginator.num_pages else data.paginator.num_pages+1
    # display_page_range = range(page_number_start, page_number_end)

    return render(request, 'user/user_listing.html', locals())

@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def add_user(request, user_location=None):
    heading = "Add User"
    groups = Group.objects.all()
    partners = Partner.objects.all()

    if True:
        if request.method == 'POST':
            try:
                data = request.POST
                username = data.get('username')
                password = data.get('password1')
                partner = data.get('partner')
                user_role = data.get('user_role')
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                email = data.get('email')

                user = User.objects.create_user(username, password)

                user.email =  email
                user.first_name = first_name
                user.last_name = last_name
                user.groups.add(Group.objects.get(id = user_role ))
                user.save()

                user_role_config = UserPartnerMapping.objects.create(
                    user=user, partner = Partner.objects.get(id = partner)
                )

                return redirect('mis:user_listing')

                # user.groups.add(user_location)
                # user_role_config = UserRoleLocationLevelConfig.objects.create(
                #     user=user, group_id=user_location, location_hierarchy_type=user_content_type)
                # for location_id in selected_user_location:
                #     user_role_location = UserLocationRelation.objects.create(
                #         UserRoleLocationLevelConfig=user_role_config, object_id=location_id, content_type=user_content_type)
            
            except ObjectDoesNotExist:
                return redirect('mis:add_user')
            return redirect('mis:user_listing')
        return render(request, 'user/add_user.html', locals())
    else:
        if request.method == 'POST':
            data = request.POST
            username = data.get('username')
            password = data.get('password1')
            partner = data.get('partner')
            user_role = data.get('user_role')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')

            if User.objects.filter(username__iexact=username).exists():
                user_location = None
                # selected_group = None
                user_exist_error = 'Username already exist'
            else:
                # selected_group = groups.get(id=user_role)
                selected_role_model = user_group_dict.get(
                    user_role)._meta.model_name
                # dropdown_value = user_group_dict.get(
                #     selected_group.name).objects.filter(active=2)
                states = State.objects.filter(active=2)
                heading = username  # + ' - '+selected_group.name
            return render(request, 'user/add_user.html', locals())
        return render(request, 'user/add_user.html', locals())

@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def user_profile(request, id):
    user = User.objects.get(id=id)
    # user_location_relation = UserPartnerMapping.objects.filter(
    #     UserRoleLocationLevelConfig__user=user, active=2).order_by('object_id')
    return render(request, 'user/user_profile.html', locals())

@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def edit_user(request, id):
    groups = Group.objects.all()
    partners = Partner.objects.all()

    user = User.objects.get(id=id)
    user_partner_config = UserPartnerMapping.objects.get(
        user=user)
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        user_role = data.get('user_role')
        partner = data.get('partner')
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        if user_role:
            user.groups.clear()
            user.groups.add( Group.objects.get(id = user_role))
        user.save()
        
        if partner:
            user_partner_config.partner = Partner.objects.get(id = partner)
        user_partner_config.save()

        return redirect('mis:user_profile', id = id)
    
    return render(request, 'user/edit_user.html', locals())


@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def deactivate_user(request, user_id):
    user = User.objects.get(id=user_id)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect('mis:user_profile', user_id=user_id)

@ login_required(login_url='/')
# @ user_passes_test(lambda u: u.is_superuser)
def user_change_password(request, id):
    user = User.objects.get(id = id)
    if request.method == 'POST':
        data = request.POST
        password = data.get('password1')
        user.set_password(password)
        user.save()
        return redirect('mis:user_profile', id = id)
    return render(request, 'user/user_change_password.html', locals())

@csrf_exempt 
def project_list_filter(request):
    if request.method == "POST":
        mission_id =request.POST.get('mission_id')
        if mission_id:
            project_obj =  Project.objects.filter(active=2).filter(partner_mission_mapping__mission__id = mission_id)
        data=list(project_obj.values('id',"name").order_by("name"))
        return HttpResponse(json.dumps(data), content_type="application/json")   

# from mis.models import Task
# from application_master.models import Project
# from mis.views import *
# from django.contrib.auth.models import User

# def task_create():
#      for user_obj in User.objects.filter(is_superuser = False):
#          if user_obj:
#             for project_obj in Project.objects.filter(active=2):
#                 print(project_obj.name)
#                 added = Task(project = project_obj,user=user_obj, name = project_obj.name, start_date="2022-08-01",end_date= "2022-08-30")
#                 added.save()

