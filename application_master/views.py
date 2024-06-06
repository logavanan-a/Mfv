from django.shortcuts import render
from . models import *
from . forms import *
from django.apps import apps
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from mis . views import *
# Create your views here.
from django.db import transaction


def master_list_form(request,model):
    heading = 'user profile'    
    page = request.GET.get('page', '1')
    state= State.objects.filter(active=2).order_by('name')
    district= District.objects.filter(active=2).order_by('name')
    partner = Partner.objects.filter(active=2).order_by('name')
    search = request.GET.get('search', '')
    state_name = request.GET.get('state_name','')
    district_name = request.GET.get('district_name','')
    partner_name = request.GET.get('partner_name', '')
    state_names= int(state_name) if state_name != '' else ''
    district_names= int(district_name) if district_name != '' else ''
    partner_names= int(partner_name) if partner_name != '' else ''
    headings={
        "state":"State",
        "district":"District",
        "mission":"Mission",
        "partner":"Partner",
        "project":"Project",
        "donor":"Donor"      
    }
    heading=headings.get(model,model)
    orderlist='name' if model != 'userprofile' else 'user__username'
    if model != 'userprofile':
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    else:
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    objects=listing_model.objects.all().order_by('-id')

    if search and model == 'userprofile':
        objects=objects.filter(user__username__icontains=search).order_by('-id')
    elif search:
        objects=objects.filter(name__icontains=search).order_by('-id')
   
    if model =='vendor':
        if state_name :
            objects=objects.filter(id=state_name).order_by('-id')
    else:
        if state_name :
            objects=objects.filter(state__id=state_name).order_by('-id')
    
    if partner_name:
        objects=objects.filter(partner__id=partner_name)


    if state_name and model == '':
        objects=objects.filter(id=state_name).order_by('-id')
    if model =='visioncenter' or model =='partner' or model =='vendor':
        if state_name:
            objects=objects.filter(district__state__id=state_name).order_by('-id')
            district_obj= District.objects.filter(active=2, state_id=state_name)
        if district_names:
            objects=objects.filter(district_id=district_names).order_by('-id')
                
    data = get_pagination(request, objects)
    
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'user/list_form.html', locals())

def master_add_form(request, model):
    if model == 'userprofile':
        heading='user profile'
    else:
        heading=model
    user_form = eval(model.title()+'Form') 
    forms=user_form()

    if request.method == 'POST':
        fields = user_form(request.POST, request.FILES)
        if fields.is_valid():
            instance = fields.save()
            instance.code = instance.name
            instance.save()
            return redirect('/application_master/list/'+str(model))
        else:
            message = [str(fields.errors[error][0]) for error in fields.errors.as_data()]
            error=''.join(message)
    return render(request, 'user/edit_form.html', locals())

def master_edit_form(request,model,id):
    if model == 'userprofile':
        heading='user profile'
    else:
        heading=model
    if model == 'partner':
        part = Partner.objects.filter(id=id).values_list('id', flat=True)
        user_prop = UserPartnerMapping.objects.filter(partner_id__in = part)
    if model == 'project':
        part = Project.objects.filter(id=id).values_list('id', flat=True)
        user_prop = UserProjectMapping.objects.filter(project_id__in = part)
    if model != 'userprofile':
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    else:
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    obj=listing_model.objects.get(id=id)
    user_form = eval(model.title()+'Form') 
    forms=user_form(request.POST or None,instance=obj)
    if request.method == 'POST' and forms.is_valid():
        page = request.GET.get('page')
        forms.save()
        return redirect('/application_master/list/'+str(model)+'/?page='+str(page))
    else:
        message = [str(forms.errors[error][0]) for error in forms.errors.as_data()]
        error=''.join(message)
    return render(request, 'user/edit_form.html', locals())


def delete_record(request,model,id):
    page = request.GET.get('page')
    
    if model != 'userprofile':
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    else:
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    obj=listing_model.objects.get(id=id)
    if obj.active == 2:
        obj.active=1
    else:
        obj.active=2
    obj.save()
    return redirect('/application_master/list/'+str(model)+'/?page='+str(page))


def master_details_form(request,model,id):
    heading=model
    if model == 'partner':
        heading="Partner"
        # donor_val = UserPartnerMapping.objects.filter(partner__id=id)
        # model_name=Partner.objects.get(id=id).id
        # groups = Group.objects.all()
        user_mapping = UserPartnerMapping.objects.filter(partner_id=id).values_list('user_id', flat=True)
        user_obj = User.objects.filter(id__in=user_mapping)
        groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        print(user_mapping,'----------user_mapping')
        print(User.objects.all(),'-user_obj---------')
        print(groups_obj,'-groups_obj---------')
    elif model == 'project':
        heading="Project"
        donor_val = UserProjectMapping.objects.filter(project__id=id)
        model_name=Project.objects.get(id=id).id
        groups = Group.objects.all()
        user_mapping = UserProjectMapping.objects.filter(project_id=id).values_list('user_id', flat=True)
        user_obj = User.objects.filter(id__in=user_mapping)
        groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        try:
            user_mapping = UserPartnerMapping.objects.get(partner_id=model_name).user.id
        except:
            user_mapping = ''
    
    listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    obj=listing_model.objects.get(id=id)
    return render(request, 'user/details_list.html', locals())


def vendor_partner_user_mapping(request,vendor_partner_id,model):
    # heading = 'user profile'
    if model == 'partner':
        partner_name=Partner.objects.get(id=vendor_partner_id).name
        heading = 'User Partner Mapping'
        try:
            user_mapping = UserPartnerMapping.objects.filter(partner_id=vendor_partner_id).values_list('user_id', flat=True)
            user_obj = User.objects.filter(id__in=user_mapping)
            groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        except:
            user_mapping = None
            user_obj = None
            groups_obj = None
        
    if model == 'project':
        vendor_name=Project.objects.get(id=vendor_partner_id).name
        heading = 'User Project Mapping'
        
        try:
            user_mapping = UserProjectMapping.objects.filter(project_id=vendor_partner_id).values_list('user_id', flat=True)
            user_obj = User.objects.filter(id__in=user_mapping)
            groups_obj = Group.objects.filter(user__in=user_obj).distinct()
            
        except:
            user_mapping = None
            user_obj = None
            groups_obj = None
        
    if request.method == 'POST':
        try:
            with transaction.atomic():
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                first_name = request.POST.get('first_name')
                if User.objects.filter(email=email).exclude(id=user_mapping).exists():
                    email_exist = "Email already exists"
                    return render(request, 'user/add_user_link_to_role.html', locals())
                if User.objects.filter(username=username).exclude(id=user_mapping).exists():
                    user_exist = "Username already exists"
                    return render(request, 'user/add_user_link_to_role.html', locals())
                if user_mapping:
                    user_obj.email = email
                    user_obj.username = username.lower()
                    user_obj.first_name=first_name

                    user_obj.save()
                    user_profile.user.set_password(password)
                    user_profile.save()
                else:
                    if User.objects.filter(email=email).exclude(id=user_mapping).exists():   
                        email_exist = "email already exists"
                        return render(request, 'user/add_user_link_to_role.html', locals())
                    user=User.objects.create_user(username=username.lower(),password=password, first_name=first_name, email=email)
                    user.save()
                    if model == 'partner':
                        partner_obj=UserPartnerMapping.objects.create(
                            partner_id = vendor_partner_id,
                            user_id = user.id
                        )
                        partner_obj.save()
                    if model == 'project':
                        vendor_obj=UserProjectMapping.objects.create(
                            project_id = vendor_partner_id,
                            user_id = user.id
                        )
                        vendor_obj.save()
                    
            return redirect('/user_listing/')
        except Exception as e:
            error = f"User is not created. Please try again. Error: {str(e)}"
    return render(request, 'user/add_user_link_to_role.html', locals())


def partner_mission_mapping_list(request, partner_id):
    heading = 'Partner Mission Mapping'
    part=Partner.objects.filter(id=partner_id)
    parner_mission_obj = PartnerMissionMapping.objects.filter(partner__id__in=part)
    data = get_pagination(request, parner_mission_obj)
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'user/partner_mission_mapping.html', locals())

def partner_mission_mapping(request, partner_id):
    heading = 'Partner Mission mapping'
    ptr = Partner.objects.get(id=partner_id)
    donor_parner_obj = UserPartnerMapping.objects.filter(partner__id=partner_id).values_list('user_id', flat=True)
    user_obj = Mission.objects.filter(active=2).order_by('name')

    donor_parner_obj = UserPartnerMapping.objects.filter(partner__id=partner_id)
    if request.method == "POST":
        data = request.POST
        mission = request.POST.get('mission')
        obj = PartnerMissionMapping.objects.create(
                partner_id=partner_id,
                mission_id=mission,
            )
        obj.save()
        return redirect('/application_master/partner_mission_mapping_list/'+str(partner_id)+'/')      
    return render(request, 'user/user_partner_mapping.html', locals())



def project_donor_mapping_list(request, project_id):
    heading = 'Project Donor Mapping'
    project_obj=Project.objects.filter(id=project_id)
    donor_project_obj = ProjectDonorMapping.objects.filter(project__id__in=project_obj)
    print(donor_project_obj,'-------------------donor_project_obj')
    data = get_pagination(request, donor_project_obj)
    current_page = request.GET.get('page', 1)
    page_number_start = int(current_page) - 2 if int(current_page) > 2 else 1
    page_number_end = page_number_start + 5 if page_number_start + \
        5 < data.paginator.num_pages else data.paginator.num_pages+1
    display_page_range = range(page_number_start, page_number_end)
    return render(request, 'user/project_donor_mapping.html', locals())


def project_donor_mapping(request, project_id):
    heading = 'Project Donor mapping'
    ptr = Project.objects.get(id=project_id)
    donor_parner_obj = ProjectDonorMapping.objects.filter(project_id=project_id)
    user_obj = Donor.objects.filter(active=2).order_by('name')

    donor_parner_obj = ProjectDonorMapping.objects.filter(project_id=project_id)
    if request.method == "POST":
        data = request.POST
        donor = request.POST.get('donor')
        obj = ProjectDonorMapping.objects.create(
                project_id=project_id,
                donor_id=donor,
            )
        obj.save()
        return redirect('/application_master/project_donor_mapping_list/'+str(project_id)+'/')      
    return render(request, 'user/donor_project_mapping.html', locals())




# def add_user(request, user_location=None):
#     """
#     Renders the add user page and handles the creation of a new user.
#     """
#     heading = "Add User"
#     groups = Group.objects.all()
#     partners = Partner.objects.all()

#     if True:
#         if request.method == 'POST':
#             try:
#                 data = request.POST
#                 username = data.get('username')
#                 password = data.get('password1')
#                 partner = data.get('partner')
#                 user_role = data.get('user_role')
#                 first_name = data.get('first_name')
#                 last_name = data.get('last_name')
#                 email = data.get('email')

#                 user = User.objects.create_user(username, password)

#                 user.email =  email
#                 user.first_name = first_name
#                 user.last_name = last_name
#                 user.groups.add(Group.objects.get(id = user_role ))
#                 user.save()

#                 user_role_config = UserPartnerMapping.objects.create(
#                     user=user, partner = Partner.objects.get(id = partner)
#                 )

#                 return redirect('mis:user_listing')
#             except ObjectDoesNotExist:
#                 return redirect('mis:add_user')
#             return redirect('mis:user_listing')
#         return render(request, 'user/add_user.html', locals())
    