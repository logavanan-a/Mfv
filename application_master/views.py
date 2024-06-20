from django.shortcuts import render
from . models import *
from . forms import *
from django.apps import apps
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from mis . views import *
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import generics as g
from django.contrib.auth.models import User
from rest_framework import permissions
from django.db import transaction
from rest_framework.views import APIView
from application_master.serializers import LoginAndroidSerializer

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
            if model == 'project':
                donor = request.POST.get('donor')
                ProjectDonorMapping.objects.update_or_create(
                    project_id=instance.id,
                    defaults={'donor_id': donor}
                )
            
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
        project_donor_obj = ProjectDonorMapping.objects.filter(project_id=id).values_list('donor_id', flat=True)
        donor = Donor.objects.filter(id__in=project_donor_obj).first()

    if model != 'userprofile':
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    else:
        listing_model = apps.get_model(app_label= 'application_master', model_name=model)
    obj=listing_model.objects.get(id=id)
    user_form = eval(model.title()+'Form') 
    forms=user_form(request.POST or None, request.FILES or None,instance=obj)
    if request.method == 'POST' and forms.is_valid():
        page = request.GET.get('page')
        forms.save()
        if model == 'project':
            donor = request.POST.get('donor')
            proj_donor = ProjectDonorMapping.objects.update_or_create(
                project_id=id,
                defaults={'donor_id': donor}
            )
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

def partner_mission_status_update(request, dpl_id):
    dpl_data=PartnerMissionMapping.objects.get(id=dpl_id)
    if dpl_data.active == 2:
        dpl_data.active = 1
    else:
        dpl_data.active = 2
    dpl_data.save()
    return redirect('/application_master/details/partner/'+str(dpl_data.partner.id)+'/')      


def master_details_form(request,model,id):
    heading=model
    if model == 'partner':
        heading="Partner"
        user_mapping = UserPartnerMapping.objects.filter(partner_id=id).values_list('user_id', flat=True)
        user_obj = User.objects.filter(id__in=user_mapping)
        groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        part=Partner.objects.filter(id=id)
        parner_mission_obj = PartnerMissionMapping.objects.filter(partner_id__in=part).order_by('-id')
    elif model == 'project':
        heading="Project"
        user_mapping = UserProjectMapping.objects.filter(project_id=id).values_list('user_id', flat=True)
        user_obj = User.objects.filter(id__in=user_mapping)
        groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        project_donor_obj = ProjectDonorMapping.objects.filter(project_id=id).values_list('donor_id', flat=True)
        project_obj = Donor.objects.filter(id__in=project_donor_obj)
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
        partner_name=Partner.objects.filter(id=vendor_partner_id)
        heading = 'User Partner Mapping'
        try:
            user_mapping = UserPartnerMapping.objects.filter(partner_id=vendor_partner_id).values_list('user_id', flat=True)
            user_obj = User.objects.filter(id=vendor_partner_id)
            groups_obj = Group.objects.filter(user__in=user_obj).distinct()
        except:
            user_mapping = None
            user_obj = None
            groups_obj = None
        
    if model == 'project':
        vendor_name=Project.objects.filter(id=vendor_partner_id)
        heading = 'User Project Mapping'
        try:
            user_mapping = UserProjectMapping.objects.filter(project_id=vendor_partner_id).values_list('user_id', flat=True)
            user_obj = User.objects.filter(id__in=user_mapping)
            groups_obj = Group.objects.filter(user__in=user_obj).distinct()
            
        except:
            user_mapping = None
            user_obj = None
            groups_obj = None
        
    groups = Group.objects.all()
    partners = Partner.objects.all()

    if request.method == 'POST':
        try:
            data = request.POST
            username = data.get('username')
            password = data.get('password1')
            user_role = data.get('user_role')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')

            user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
            user.groups.add(Group.objects.get(id=user_role))
            user.save()
            if model == 'partner':
                user_role_config = UserPartnerMapping.objects.create(user=user, partner_id=vendor_partner_id)
                user_role_config.save()
            elif model == 'project':
                user_role_config = UserProjectMapping.objects.create(user=user, project_id=vendor_partner_id)
                user_role_config.save()

            return redirect('/application_master/details/'+ str(model) + '/'+ str(vendor_partner_id) + '/')
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
    pmm_obj = PartnerMissionMapping.objects.filter(partner_id=partner_id).values_list('mission_id',flat=True)
    missions = Mission.objects.filter(active=2).exclude(id__in=pmm_obj).order_by('name')
    
    if request.method == "POST":
        selected_missions = request.POST.getlist('missions')  
        for mission_id in selected_missions:
            part_mission=PartnerMissionMapping.objects.create(
                partner_id=partner_id,
                mission_id=mission_id,
            )
            part_mission.save()
        return redirect('/application_master/details/partner/' + str(partner_id) + '/')
    
    return render(request, 'user/user_partner_mapping.html',locals())



def project_donor_mapping_list(request, project_id):
    heading = 'Project Donor Mapping'
    project_obj=Project.objects.filter(id=project_id)
    donor_project_obj = ProjectDonorMapping.objects.filter(project__id__in=project_obj)
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


def edit_user_partner_project(request, id, model):
    """
    Edits the user details.
    """
    groups = Group.objects.all()
    partners = Partner.objects.all()

    user = User.objects.get(id=id)
    if model == 'partner':
        vendor_id = UserPartnerMapping.objects.filter(user_id=user).values_list('partner_id', flat=True)
        vendor_partner_id = Partner.objects.filter(id__in = vendor_id).first()
    elif model == 'project':
        vendor_id = UserProjectMapping.objects.filter(user_id=user).values_list('project_id', flat=True)
        vendor_partner_id = Project.objects.filter(id__in = vendor_id).first()

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
       
        return redirect('/application_master/details/'+ str(model) + '/'+ str(vendor_partner_id.id) + '/')
    return render(request, 'user/edit_user_link_to_role.html', locals())



class LoginAndroidView(APIView):
    serializer_class = LoginAndroidSerializer
    def post(self, request, *args, **kwargs):
        """
        User Login.
        ---
        parameters:
        - name: username
          description: Username Login
          required: true
          type: string
          paramType: form
        - name: password
          description: Password for Login
          paramType: form
          required: true
          type: string
        """
        response = {}
        serializer = LoginAndroidSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(username=request.data[
                                'username'], password=request.data['password'])
            print(user, '-----------1------------')
            if user is not None:
                if user.is_superuser:
                    login(request, user)
                    response.update({
                            'status': 1, 'admin': 1,
                            'user_id': int(user.id),
                            'first_name': user.first_name
                            })
                else:
                    login(request, user)
                    response.update({'status': 1, 'admin': 0, 'user_id': int(user.id),
                                     'first_name': user.first_name
                                     })
            else:
                try:
                    user = User.objects.get(username = request.data.get('username'))
                    if user.is_active == False:
                        response.update({'status': 0, 'msg': "User is inactive"})
                    else:
                        response.update({'status': 0, 
                        'msg': "Username/Password mismatch "})
                except: 
                    response.update(
                        {'status': 0, 'msg': "Username/Password mismatch"})
        else:
            errors = serializer.errors
            errors = stripmessage(errors)
            error_dict = {}
            error_dict.update({'message':'error','status':0,'errors':errors})
            return Response(error_dict)
        return Response(response)

@method_decorator(csrf_exempt, name='dispatch')
class UserlistAndroid(g.CreateAPIView):

    # authentication_class = (ExpiringTokenAuthentication,)
    # permission_classes = (permissions.IsAuthenticated,)

    def post(cls, request, format=None):
        """
        API of users for android
        ---
        parameters:
        - name: user_id
          description: Pass user id
          required: true
          type: integer
          paramType: form
        """
        data = request.data
        if not data.get('user_id'):
            return Response({'status':0,'message':'user id required'})
        try:
            userlist = User.objects.filter().order_by("-id")
            response=[]
            for i in userlist:
                user_info = {'id': i.id,
                         'name': i.get_full_name(),
                         'username':i.username,
                         'email': i.email,
                         'mobile_number': "",
                         }
                # role_obj = UserRoles.objects.get_or_none(user = i)
                # if role_obj:
                #     role_id = all()[0].user_role_ids()
                # else:
                role_id = i.groups.all()[0].id
                user_info.update(role_id = role_id)
                response.append(user_info)
            return Response({'message':'success','status':2,'users':response})
        except Exception as e:
            response = [{'message': e.args[0], 'status': 0}]
        return Response(response)

def stripmessage(errors):
    for i, j in errors.items():
        errors[i] = j[0]
        expr = re.search(r'\w+:', errors[i])
        if expr:
            ik = expr.group().replace(':', '')
            errors[ik] = errors.pop(i)
            errors[ik] = re.sub(r'\w+:', '', errors[ik])
    return errors