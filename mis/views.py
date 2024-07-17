import json
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

# import requests
from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget, Partner,
                                       PartnerMissionMapping, Project,
                                       ProjectDonorMapping, ProjectFiles,
                                       State, UserPartnerMapping, UserProjectMapping,UserProfile)
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
from django.db.models import Q

pg_size = 10
def get_pagination(request, users):
    """
    Paginates a list of users based on the request parameters.
    It uses the Django Paginator class to divide the users into multiple pages.
    The current page number is extracted from the request.GET parameters.
    The paginated users are then returned as the result.
    """
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
    """
    The login function retrieves the username and password from the request and proceeds to authenticate the user. 
    If the user is valid, the function stores the user details in the session.
    """
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
            if user.groups.filter(name__in = ['Partner Data Entry Operator','Partner Admin','Project In-charge']).exists():# project incharge
                user_project=UserProjectMapping.objects.filter(user=request.user,active=2).select_related('project','project__partner_mission_mapping','project__partner_mission_mapping__partner','project__partner_mission_mapping__mission','project__district','project__district__state')
                user_project_ids = user_project.values_list('project__id',flat=True)
                user_partner_id = user_project.values_list('project__partner_mission_mapping__partner_id',flat=True)
                user_mission_id = user_project.values_list('project__partner_mission_mapping__mission_id',flat=True)

                user_donor_id=ProjectDonorMapping.objects.filter(project__id__in=user_project_ids,active=2).values_list('donor__id',flat=True).distinct()
                user_category_list=MissionIndicatorCategory.objects.filter(mission__id__in=user_mission_id,active=2).values_list('id',flat=True)
                user_parent_boundary_list = user_project.values_list('project__district__state_id',flat=True)
                user_boundary_list = user_project.values_list('project__district_id',flat=True)
            elif user.is_superuser:
                user_mission_id=Mission.objects.filter(active=2).values_list('id',flat=True)
                user_project_ids=Project.objects.filter(active=2).values_list('id',flat=True)
                user_partner_id=Partner.objects.filter(active=2).values_list('id',flat=True)
                user_donor_id=Donor.objects.filter(active=2).values_list('id',flat=True).distinct()
                user_category_list=MissionIndicatorCategory.objects.filter(active=2).values_list('id',flat=True)
                user_parent_boundary_list = State.objects.filter(active=2).values_list('id',flat=True)
                user_boundary_list = District.objects.filter(active=2).values_list('id',flat=True)
            
            request.session['user_mission_list']=list(user_mission_id)
            request.session['user_project_list']=list(user_project_ids)
            request.session['user_partner_list']=list(user_partner_id)
            request.session['user_donor_list']=list(user_donor_id)
            request.session['user_category_list']=list(user_category_list)
            request.session['user_parent_boundary_list']=list(user_parent_boundary_list)
            request.session['user_boundary_list']=list(user_boundary_list)
            try:
                #need to check if used or not and remove 
                user_partner = UserPartnerMapping.objects.get(user = user)
                partner_mission_mapping_id = PartnerMissionMapping.objects.filter(mission__id__in= [1,2],partner=user_partner.partner).values_list('id', flat = True)
                request.session['user_partner'] = user_partner.partner.name
                request.session['partner_mission_mapping_id'] = list(partner_mission_mapping_id)
                
            except:
                user_partner = ''              
            return redirect('/task-list/')
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
    """
    View function to add a mission indicator achievement.
    Requires the user to be logged in.
    Retrieves the mission, program and finance categories,
    and the task associated with the provided slug and task_id.
    """
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    task_obj = Task.objects.get(id = task_id)
    user = get_user(request)
    user_role = str(user.groups.last())
    if slug == 'mission-jyot':
        v_calc_dict={
            46:1,
            47:1,
            48:1,
            292:2,
            49:2,
            293:2,

            301:3,
            302:3,
            303:3,
            304:4,
            305:4,
            306:4,
        }
        total_cal_dict={
            48:[46,47],
            293:[292,49],
            349:[293,48],

            303:[301,302],
            306:[304,305],
            307:[303,306],
        }
        read_only_field=[349,307]
        mission_jyot_column_total_ids=[48,293,303,306]
    else:
        v_calc_dict={}
        total_cal_dict={}
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

    return render(request, 'mis/indicator_list.html', locals())

@login_required(login_url='/')
def missionindicator_edit(request, slug, id,task_id):
    """
    View function to edit a mission indicator achievement.
    Requires the user to be logged in.
    Retrieves the mission, program and finance categories,
    the mission indicator achievement with the provided id,
    and the task associated with the provided slug and task_id.
    """
    mission_obj = Mission.objects.get(slug = slug)
    heading = mission_obj.name
    mission_respose_obj = MissionIndicatorAchievement.objects.get(id = id)
    programe_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '1', active=2).order_by('listing_order')
    finance_category = MissionIndicatorCategory.objects.filter(mission__slug = slug,category_type = '2', active=2).order_by('listing_order')
    user = get_user(request)
    user_role = str(user.groups.last())

    dataentry_obj = DataEntryRemark.objects.filter(task__id=task_id, remark__isnull=False).order_by('-id')
    reject_obj = DataEntryRemark.objects.filter(task_id=task_id,reject_reason__isnull=False).order_by('-id')
    if slug == 'mission-jyot':
        v_calc_dict={
            46:1,
            47:1,
            48:1,
            292:2,
            49:2,
            293:2,

            301:3,
            302:3,
            303:3,
            304:4,
            305:4,
            306:4,
        }
        total_cal_dict={
            48:[46,47],
            293:[292,49],
            349:[293,48],

            303:[301,302],
            306:[304,305],
            307:[303,306],
        }
        read_only_field=[349,307]
        mission_jyot_column_total_ids=[48,293,303,306]
    else:
        v_calc_dict={}
        total_cal_dict={}
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
    """
    View function to display a list of tasks.
    Requires the user to be logged in.
    Retrieves the tasks based on various filters provided in the request.
    Renders the task_list.html template with the task objects.
    """
    heading= 'Task List'
    user = get_user(request)

    previous_month = datetime.now() - relativedelta(months=1)
    below_last_two_month = datetime.now().date() - relativedelta(months=2)

    mission_objs = Mission.objects.filter(active=2,id__in=request.session['user_mission_list'])
    project_objs = Project.objects.filter(active=2,id__in=request.session['user_project_list'],application_type_id=510).order_by('name')
    partner_objs = Partner.objects.filter(active=2,id__in=request.session['user_partner_list']).order_by('name')
    filter_data = request.GET
    archive = filter_data.get('archive') if(filter_data.get('archive') != 'None') else None
    mission = filter_data.get('mission') if(filter_data.get('mission') != 'None') else None
    project = filter_data.get('project') if(filter_data.get('project') != 'None') else None
    partner = filter_data.get('partner') if(filter_data.get('partner') != 'None') else None
    partners = int(partner) if partner not in [None, 'None', ''] else None

    task_status = filter_data.get('task_status') if(filter_data.get('task_status') != 'None') else None
    month = filter_data.get('month') if(filter_data.get('month') != 'None') else None
    year = filter_data.get('year') if(filter_data.get('year') != 'None') else None
    month_year = filter_data.get('month_year') if(filter_data.get('month_year') != 'None') else None

    if(archive != None or month_year != None or project != None or mission != None or task_status != None) and (archive != None):
        task_obj = Task.objects.filter(task_status=4,active=2).order_by('project__partner_mission_mapping__partner__name')
    else:
        task_obj = Task.objects.filter(~Q(task_status=4),active=2).order_by('project__partner_mission_mapping__partner__name')
    
    if mission:
        project_objs = project_objs.filter(active=2, partner_mission_mapping__mission__id = mission)
        task_obj = task_obj.filter(project__partner_mission_mapping__mission__id = mission)

    if partner:
        project_objs = project_objs.filter(active=2, partner_mission_mapping__partner__id = partner)
        task_obj = task_obj.filter(project__partner_mission_mapping__partner__id = partner)

    if project:
        task_obj = task_obj.filter(project__id = project)
    
    if task_status:
        task_obj = task_obj.filter(task_status = task_status)

    if month_year:
        if archive:
            month_year_date = datetime.strptime(month_year, '%B %Y')
            task_obj = task_obj.filter(start_date__year=month_year_date.year, start_date__month=month_year_date.month)

    if year:
        task_obj = task_obj.filter(start_date__year = year)
    
    if month:
        task_obj = task_obj.filter(start_date__month = month)

    #TODO: need to use the user project mapping 
    # if user.groups.filter(name = 'Partner Admin').exists():
    #     user_lists = UserPartnerMapping.objects.get(user = request.user)
    #     for partner_list in UserPartnerMapping.objects.filter(partner = user_lists.partner):
    #         task_obj = task_obj.filter(active=2, project__partner_mission_mapping__partner = partner_list.partner).order_by('-start_date')
    
    # elif user.groups.filter(name = 'Project In-charge').exists():
        # task_obj = task_obj.filter(active=2, project_in_charge = request.user).order_by('-start_date')
    if not user.is_superuser:
        task_obj = task_obj.filter(active=2, project_id__in = request.session.get('user_project_list',[])).order_by('-start_date')
    # else:
    #     user_lists = UserPartnerMapping.objects.get(user = request.user)
    #     for partner_list in UserPartnerMapping.objects.filter(partner = user_lists.partner):
            # task_obj = task_obj.filter(active=2, user = request.user, project__partner_mission_mapping__partner = partner_list.partner).order_by('-start_date')
    
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
    """
    View function to change the status of a task.
    Retrieves the task object with the provided task_id.
    If the request method is POST, updates the task status and saves the changes.
    Returns a JSON response indicating the success of the operation.
    """
    if request.method == "POST":
        status_val = request.POST.get('status_val')
        remark =request.POST.get('remark')
        reject_reason =request.POST.get('reject_reason')
        task_obj = Task.objects.get(id = task_id)
        task_obj.task_status = status_val
        task_obj.save()
        if remark:
            DataEntryRemark.objects.create(task = task_obj, remark = remark, user_name = request.user)
        if reject_reason:
            DataEntryRemark.objects.create(task = task_obj, reject_reason = reject_reason, user_name = request.user)
        return HttpResponse({"message":'true'} , content_type="application/json")
    return HttpResponse({"message":'false'}, content_type="application/json")  

@login_required(login_url='/')
def project_list(request):
    """
    View function to display a list of projects.
    Retrieves the partner associated with the logged-in user.
    Retrieves the IDs of partner mission mappings for the partner.
    Retrieves the projects associated with the partner mission mappings and specific missions.
    Paginates the project list.
    """
    heading= 'Project List'
    partner = UserPartnerMapping.objects.get(user = request.user).partner
    partner_mission_mapping_ids = PartnerMissionMapping.objects.filter(partner = partner).values_list('id', flat=True)
    project_obj = Project.objects.filter(partner_mission_mapping__id__in = partner_mission_mapping_ids, partner_mission_mapping__mission__id__in = [2,1],application_type_id=510)
    object_list = get_pagination(request, project_obj)

    page_number_display_count = 5
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + page_number_display_count if page_number_start + \
        page_number_display_count < object_list.paginator.num_pages else object_list.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'project/project_list.html', locals())

def get_district(request, state_id):
    """
    Ajax view function to retrieve the districts based on the selected state.
    Retrieves the districts associated with the specified state.
    Returns the districts as a JSON response.
    """
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
        """
        Handles the GET request to display the project add form.
        Retrieves the necessary data for rendering the form.
        """
        heading= 'Project Add'
        states = State.objects.all()
        # districts = District.objects.all()
        mission_obj = PartnerMissionMapping.objects.filter(id__in = request.session['partner_mission_mapping_id'])
        return render(request,self.template_name,locals())

    @method_decorator(login_required(login_url='/'))
    def post(self, request):
        """
        Handles the POST request to add a new project.
        Creates a new project based on the submitted form data.
        """
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
        project_add = Project.objects.create(name = name, start_date = start_date, partner_mission_mapping = partner_mission_mapping_obj, district = district_obj, location=location,application_type_id=510 )
        return redirect('/project-list/')


class ProjectUpdate(View):
    template_name = 'project/project_add_edit.html'
    
    @method_decorator(login_required(login_url='/'))
    def get(self, request, id):
        """
        Handles the GET request to display the project update form.
        Retrieves the necessary data for rendering the form.
        """
        heading= 'Project Edit'
        states = State.objects.all()
        mission_obj = PartnerMissionMapping.objects.filter(id__in = request.session['partner_mission_mapping_id'])
        project_obj = Project.objects.get(id = id)
        districts = District.objects.filter(id = project_obj.district.id)
        return render(request,self.template_name,locals())

    @method_decorator(login_required(login_url='/'))
    def post(self, request, id):
        """
        Handles the POST request to update a project.
        Updates the project based on the submitted form data.
        """
        data = request.POST
        name = data.get('name')
        district = data.get('district')
        location = data.get('location')
        start_date = data.get('start_date')
        district_obj = District.objects.get(id = district)
        project_update = Project.objects.get(id = id)
        project_update.name = name
        project_update.start_date = start_date
        project_update.district = district_obj
        project_update.location = location
        project_update.save()
                
        return redirect('/project-list/')

@ login_required(login_url='/')
def user_listing(request):
    """
    Renders the user listing page.
    Displays a list of user roles and locations.
    """
    heading = "User Management"
    search = request.GET.get('search', '')
    user_role_location_config = UserProfile.objects.filter(
        active=2).order_by('user__username')
    groups = Group.objects.all().exclude(id=11)
    if search:
        user_role_location_config = user_role_location_config.filter(user__username__icontains = search, active=2)
    
    object_list = get_pagination(request, user_role_location_config)
    
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < object_list.paginator.num_pages else object_list.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)

    return render(request, 'user/user_listing.html', locals())

@ login_required(login_url='/')
def add_user(request, user_location=None):
    """
    Renders the add user page and handles the creation of a new user.
    """
    heading = "Add User"
    groups = Group.objects.filter()
    partners = Partner.objects.all()

    if request.method == 'POST':
        try:
            # import ipdb; ipdb.set_trace()
            data = request.POST
            username = data.get('username')
            password = data.get('password1')
            partner = data.get('partner')
            user_role = data.get('user_role')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            login_type = data.get('login_type')
            mobile_no = data.get('mobile_no')
            if User.objects.filter(username__iexact=username).exists():
                user_location = None
                user_exist_error = 'Username already exist'
                return render(request, 'user/add_user.html', locals())
            if User.objects.filter(email__iexact=email).exists():
                user_location = None
                user_exist_error = 'Email already exist'
                return render(request, 'user/add_user.html', locals())
            if UserProfile.objects.filter(phone_no__iexact=mobile_no).exists():
                user_location = None
                user_exist_error = 'Mobile no already exist'
                return render(request, 'user/add_user.html', locals())
            user = User.objects.create_user(username, password)
            user.email =  email
            user.first_name = first_name
            user.last_name = last_name
            user.groups.add(Group.objects.get(id = user_role ))
            user.save()

            # user_role_config = UserPartnerMapping.objects.create(
            #     user=user, partner = Partner.objects.get(id = partner)
            # )
            user_profile=UserProfile.objects.create(user=user, phone_no=mobile_no, login_type=login_type)
            user_profile.save()
            return redirect('mis:user_listing')
        except:
            user.delete()
            return redirect('mis:add_user')
    return render(request, 'user/add_user.html', locals())
    
@ login_required(login_url='/')
def user_profile(request, user_id):
    """
    Renders the user profile page.
    """
    user = User.objects.get(id=user_id)
    user_profile_obj = UserProjectMapping.objects.filter(user=user)

    return render(request, 'user/user_profile.html', locals())

    

@ login_required(login_url='/')
def add_map_project(request, user_id):
    heading = "Add User Project Mapping"

    states = State.objects.filter(active=2).order_by('name')
    districts = District.objects.filter(active=2).order_by('name')
    donors = Donor.objects.filter(active=2)
    partner_mission = PartnerMissionMapping.objects.filter()
    if request.method == 'POST':
        name = request.POST.get('name')
        partner_mission = request.POST.get('partner_mission')
        state = request.POST.get('state')
        district = request.POST.get('district')
        location = request.POST.get('location')
        donor = request.POST.get('donor')
        start_date = request.POST.get('start_date',None)
        end_date = request.POST.get('end_date',None)

        additional_info = request.POST.get('additional_info',None)
        pro_details = Project.objects.create(
            name=name,
            partner_mission_mapping_id=partner_mission,
            district_id=district,
            location=location,
            additional_info=additional_info,
            start_date=start_date,
            end_date=end_date,    
            application_type_id=510,        
        )
        pro_details.save()
        user_project_mapping= UserProjectMapping.objects.create(
            project_id=pro_details.id,
            user_id=user_id
        )
        user_project_mapping.save()
        project_donor_mapping =ProjectDonorMapping.objects.create(
                    project_id=pro_details.id,
                    donor_id=donor
                )
                    # defaults={'donor_id': donor}
                
        return redirect('/user-profile/'+ str(user_id) + '/')

    return render(request, 'user/adding_project.html', locals())

@ login_required(login_url='/')
def edit_user(request, id):
    """
    Edits the user details.
    """
    groups = Group.objects.all()
    partners = Partner.objects.all()

    user = User.objects.get(id=id)
    user_profile = UserProfile.objects.get(user=user)
    # user_partner_config = UserPartnerMapping.objects.get(
    #     user=user)
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        user_role = data.get('user_role')
        partner = data.get('partner')
        login_type = data.get('login_type')
        mobile_no = data.get('mobile_no')
        if User.objects.filter(username__iexact=username).exclude(id=user.id).exists():
            user_location = None
            user_exist_error = 'Username already exist'
            return render(request, 'user/add_user.html', locals())
        if User.objects.filter(email__iexact=email).exclude(id=user.id).exists():
                user_location = None
                user_exist_error = 'Email already exist'
                return render(request, 'user/add_user.html', locals())
        if UserProfile.objects.filter(phone_no__iexact=mobile_no).exclude(id=user_profile.id).exists():
            user_location = None
            user_exist_error = 'Mobile no already exist'
            return render(request, 'user/add_user.html', locals())
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        if user_role:
            user.groups.clear()
            user.groups.add( Group.objects.get(id = user_role))
        user.save()
        user_profile.phone_no = mobile_no
        user_profile.login_type = login_type
        user_profile.save()
        # if partner:
        #     user_partner_config.partner = Partner.objects.get(id = partner)
        # user_partner_config.save()

        return redirect('mis:user_profile', id = id)
    
    return render(request, 'user/edit_user.html', locals())


@ login_required(login_url='/')
def deactivate_user(request, user_id):
    """
    Deactivates or activates a user.
    """
    user = User.objects.get(id=user_id)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect('mis:user_profile', user_id=user_id)

@ login_required(login_url='/')
def user_change_password(request, id):
    """
    Handles the change password functionality for a user.
    """
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
    """
    Filters the project list based on the selected mission.
    """
    if request.method == "POST":
        mission_id =request.POST.get('mission_id')
        if mission_id:
            project_obj =  Project.objects.filter(active=2).filter(partner_mission_mapping__mission__id = mission_id,id__in=request.session['user_project_list'],application_type_id=510)
        else:
            project_obj =  Project.objects.filter(active=2).filter(id__in=request.session['user_project_list'],application_type_id=510)
        data=list(project_obj.values('id',"name").order_by("name"))
        return HttpResponse(json.dumps(data), content_type="application/json")   

