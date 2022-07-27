import json

import requests
from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget, Partner,
                                       PartnerMissionMapping, Project,
                                       ProjectDonorMapping, ProjectFiles,
                                       State, UserPartnerMapping)
from django.conf import settings
from django.contrib.auth import authenticate, get_user, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, auth, Group
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
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    task_obj = Task.objects.get(id = task_id)
    user = get_user(request)
    user_role = str(user.groups.last())

    if request.method == 'POST':
        data = request.POST
        working_day = request.POST.get('working_day')
        project_reference_file = request.FILES.get('project_reference_file')

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
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    user = get_user(request)
    user_role = str(user.groups.last())
    # task_obj = Task.objects.get(id = task_id)

    if request.method == 'POST':

        working_day = request.POST.get('working_day')
        project_reference_file = request.FILES.get('project_reference_file')

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


# @ login_required(login_url='/login/')
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

# @ login_required(login_url='/login/')
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


# @ login_required(login_url='/login/')
# @ user_passes_test(lambda u: u.is_superuser)
def user_profile(request, id):
    user = User.objects.get(id=id)
    # user_location_relation = UserPartnerMapping.objects.filter(
    #     UserRoleLocationLevelConfig__user=user, active=2).order_by('object_id')

    return render(request, 'user/user_profile.html', locals())


# @ login_required(login_url='/login/')
# @ user_passes_test(lambda u: u.is_superuser)
def user_role_location_delete(request, user_id, user_role_location_id=None):
    if user_role_location_id:
        user_location_relation = UserLocationRelation.objects.get(
            id=user_role_location_id)
        user_location_relation.active = 0
        user_location_relation.save()
    else:
        user_location_relation = UserLocationRelation.objects.filter(
            UserRoleLocationLevelConfig__user__id=user_id, active=2)
        user_location_relation.update(active=0)
    return redirect('child_management:user_profile', user_id=user_id)


# @ login_required(login_url='/login/')
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


# @ login_required(login_url='/login/')
# @ user_passes_test(lambda u: u.is_superuser)
def deactivate_user(request, user_id):
    user = User.objects.get(id=user_id)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect('mis:user_profile', user_id=user_id)

# @ login_required(login_url='/login/')
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



# @ login_required(login_url='/login/')
# @ user_passes_test(lambda u: u.is_superuser)
def add_location(request, user_id):
    # Group name with permission level objects
    # 12-'Central WCD Officials': Centre,
    # 11-'WAIC admin': Centre,
    # 20-'State WCD Officials': State,
    # 2-'WAIC Team Member': ShelterHome,
    # 21-'WAIC Partner User': ShelterHome,
    # 3-'WAIC Partner Admin': ShelterHome,
    # 16-'District CWC User': District,
    # 15-'District CWC Admin': District,
    # 13-'DCPU Admin': District,
    # 14-'DCPU User': District,
    # 4-'Shelter admin': ShelterHome,
    # 17-'Shelter Home User': ShelterHome,
    # 18-'SAA Admin': ShelterHome,
    # 19-'SAA User': ShelterHome,
    user_group_dict = {'12': ShelterHome,
                       '11': Centre,
                       '20': ShelterHome,
                       '2': ShelterHome,
                       '21': ShelterHome,
                       '3': ShelterHome,
                       '16': ShelterHome,
                       '15': ShelterHome,
                       '13': ShelterHome,
                       '14': ShelterHome,
                       '4': ShelterHome,
                       '17': ShelterHome,
                       '18': ShelterHome,
                       '19': ShelterHome,
                       }
    states = State.objects.filter(active=2)
    user = User.objects.get(id=user_id)
    user_role_location_config = UserRoleLocationLevelConfig.objects.get(
        user=user)
    heading = user.username + ' - '+user_role_location_config.group.name
    user_role = str(user_role_location_config.group.id)
    selected_role_model = user_group_dict.get(user_role)._meta.model_name
    # Already located location
    already_located_locations_id = UserLocationRelation.objects.filter(
        UserRoleLocationLevelConfig=user_role_location_config, active=2).values_list('object_id', flat=True)
    # User groups for already located
    located_location_for_centre, located_location_for_district, located_location_for_sheltehome = [], [], []
    if selected_role_model == 'centre':
        located_location_for_centre = already_located_locations_id
    elif selected_role_model == 'state':
        states = State.objects.exclude(id__in=already_located_locations_id)
    elif selected_role_model == 'district':
        located_location_for_district = list(already_located_locations_id)
    else:
        located_location_for_sheltehome = list(already_located_locations_id)
    if request.method == 'POST':
        data = request.POST
        user_location_centre = data.getlist('user_location_centre', '')
        user_location_state = data.getlist('user_location_state', '')
        user_location_district = data.getlist(
            'user_location_district', '')
        user_location_shelterhome = data.getlist(
            'user_location_shelterhome', '')
        # object_id based on content type
        # Selected group while adding user
        selected_places_with_role = {
            "centre": [user_location_centre, ],
            "state": [user_location_state, user_location_centre],
            "district": [user_location_district, user_location_state]
        }
        selected_user_location = selected_places_with_role.get(
            selected_role_model, [user_location_shelterhome, user_location_district])
        # For checking the exist location removed
        all_locations = []
        if selected_role_model == 'state':
            all_locations = State.objects.filter(
                active=2, centre__id__in=selected_user_location[1]).values_list('id', flat=True)
        elif selected_role_model == 'district':
            all_locations = District.objects.filter(
                active=2, state__id__in=selected_user_location[1]).values_list('id', flat=True)
        elif selected_role_model == 'shelterhome':
            all_locations = ShelterHome.objects.filter(
                active=2, district__id__in=selected_user_location[1]).values_list('id', flat=True)
        # import ipdb
        # ipdb.set_trace()
        all_locations = [str(i) for i in all_locations]
        exists_location_relation_id = set(
            all_locations) - set(selected_user_location[0])
        UserLocationRelation.objects.filter(object_id__in=list(
            exists_location_relation_id)).update(active=0)
        for location_id in selected_user_location[0]:
            if int(location_id) not in already_located_locations_id:
                user_role_location = UserLocationRelation.objects.create(
                    UserRoleLocationLevelConfig=user_role_location_config, object_id=location_id, content_type=user_role_location_config.location_hierarchy_type)
        return redirect('child_management:user_profile', user_id=user_id)
    return render(request, 'user_management/add_user.html', locals())
