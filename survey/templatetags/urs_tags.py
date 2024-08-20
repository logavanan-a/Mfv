from django import template
from constants import data
from django.contrib.auth.models import User
from application_master.models import Menus
from survey.models import *
from survey.form_views import get_result_query,get_financial_year_dates
# from projectmanagement.models import (LineitemTheme,ProjectTheme)
# from beneficiary.models import BeneficiaryResponse,BeneficiaryLink
import urllib3
import json 
register = template.Library()

# @register.filter
# def get_permission(request=''):

#     # Find Permission
#     request = data['request']
#     if request.user.is_superuser:
#         return 'superuser'
#     try:
#         return request.user.userprofile_set.get().designation.name
#     except:
#         pass

# Register function as template tag
@register.simple_tag
def get_request():
    # Takes model name as argument and return Queryset
    request = data['request']
    return request

# @register.filter
# def get_all_menus(value):
#     #
#     # filtering active menus
#     #
#     return Menus.objects.filter(active = 2).order_by('name')

### to get the role configuration object ###
# @register.filter
# def get_role_config_obj(value, rid):
#     try:
#         return RoleConfig.objects.get(menu__id = value, role__id = rid)
#     except:
#         return None

### for getting the list of menus which are assigned to a user ###
# @register.filter
# def get_user_menu_list(request):
#     user = request.user.id or None
#     menu_list = []
#     if user is not None:
#         user_role = UserRoles.objects.get(user__id = user)
#         role_ids = user_role.role_type.all().values_list('id', flat = True)
#         role_configs = RoleConfig.objects.filter(role__id__in = role_ids,
#                         view = 2).order_by('menu__name')
#         menu_ids = list(set(role_configs.values_list('menu__id', flat = True)))
#         menus = Menus.objects.filter(id__in = menu_ids, active = 2).distinct()
#         parent_menus = menus.filter(parent = None)
#         menu_list = [(menu, 
#                         [(menu1, 
#                             [(menu2, 
#                                 [(menu3, menus.filter(parent=menu3))
#                                     for menu3 in menus.filter(parent = menu2)])
#                                 for menu2 in menus.filter(parent = menu1)])
#                             for menu1 in menus.filter(parent = menu)])
#                         for menu in parent_menus]

#     return menu_list


# @register.simple_tag
# def get_login_role(request):
#     role_id = 0
#     ur = request.user.userroles.role_type.all()
#     if ur:
#         role_id = ur.latest("id").id
#     print(role_id)
#     return role_id


@register.filter
def has_permission_for_action(request, key):
 
    try:
        # 
        # Check for the permission of user for the action of menu 
        # 
        
        user = request.user or None
        menu, permission_key = key.split('&')
        success = False

        if user is not None:
            # user_role = request.session['menu_permission_data']
            # for record in user_role:
            #     if record.get(menu) and record.get(menu).get(permission_key):
            #         success = True
            #         break
            user_role = User.objects.get(id = user.id)
            for role in user_role.groups.all():
                role_config = Menus.objects.get(group = role.id,active=2,
                            slug = menu)
                if role_config:
                    success = True
                    break
    except:
        success = False
    return success

### concatenate of two strings ###
@register.filter
def make_string(val1, val2):
    return val1+"&"+val2

@register.filter
def validation_popup(survey_id, creation_key):
    start_date, end_date = get_financial_year_dates()
    query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\' @@financial_year @@survey_id'.format(creation_key)#
    query=query.replace("@@financial_year","and (js.created at time zone 'Asia/Kolkata')::date >='{0}' and (js.created at time zone 'Asia/Kolkata')::date <= '{1}'".format(start_date, end_date))
    refferal_vlu=query.replace("@@survey_id","and s.id = '{0}'".format(5))
    value = 0
    if survey_id in [6,7,8]:
        refferal_query="""with a as ("""+refferal_vlu+""") select coalesce(sum(case when response->>'344'='272' then 1 else 0 end),0) as ht from a"""
        refferal_result = get_result_query(refferal_query)[0][0]
        value = 4 if len(get_result_query(refferal_vlu)) != 0 and refferal_result == 0 else 3 
        if len(get_result_query(refferal_vlu)) != 0 and refferal_result == 1:
            value = 0
            query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\' and s.id =11 order by js.response->>\'445\''.format(creation_key)#
            if survey_id == 8:
                result=get_result_query(query)
                if len(result) == 0:
                    value = 2
                else:
                    value = 0
                    check_to_spectacle_dispensing = json.loads(result[-1][2]).get('445')
                    date1 = datetime.strptime(check_to_spectacle_dispensing, '%d-%m-%Y')
                    current_date = datetime.today()
                    date_difference = current_date - date1
                    if date_difference.days >= 90:
                        value = 1
            
    return value


        
@register.filter
def survey_show(survey_id, creation_key):
    start_date, end_date = get_financial_year_dates()
    value = False
    periodicity= list(Survey.objects.filter(periodicity=7).values_list('id',flat=True))
    periodicity.append(3)
    query='select js.id,survey_id,js.response,s.slug,creation_key,js.created,js.modified,js.active,s.extra_config from survey_jsonanswer js inner join survey_survey s on s.id = js.survey_id where js.active != 0 and js.cluster->>\'BeneficiaryResponse\' = \'{0}\' @@financial_year @@survey_id'.format(creation_key)#
    query=query.replace("@@financial_year","and (js.created at time zone 'Asia/Kolkata')::date >='{0}' and (js.created at time zone 'Asia/Kolkata')::date <= '{1}'".format(start_date, end_date))
    primary_vlu=query.replace("@@survey_id","and s.id = '{0}'".format(3))
    primary_query="""with a as ("""+primary_vlu+""") select coalesce(sum(case when response->>'250' in ('154','155') or a.response->>'252' in ('162','163') then 1 else 0 end),0) as ht from a"""
    primary = len(get_result_query(primary_vlu)) 
    primary_result = get_result_query(primary_query)[0][0] if primary != 0 else 1
    if primary_result == 0:
        value = True if survey_id == 4 else False
        secondary_vlu=query.replace("@@survey_id","and s.id = '{0}'".format(4))
        secondary = len(get_result_query(secondary_vlu))
        if secondary == 1: 
            secondary_query="""with a as ("""+secondary_vlu+""") select coalesce(sum(case when response->>'284'='180' then 1 else 0 end),0) as ht from a"""
            secondary_result = get_result_query(secondary_query)[0][0]
            value = False 
            if secondary_result == 1:
                refferal_vlu=query.replace("@@survey_id","and s.id = '{0}'".format(5))
                refferal = len(get_result_query(refferal_vlu))
                value = True if survey_id in [9,11,6,7,8,5] else False
                if refferal == 1:
                    refferal_query="""with a as ("""+refferal_vlu+""") select coalesce(sum(case when response->>'344'='272' then 1 else 0 end),0) as ht from a"""
                    refferal_result = get_result_query(refferal_query)[0][0]
                    value = False 
                    if refferal == 1 and survey_id == 5:
                        value = False 
                    elif survey_id in [9,11,6,7,8]:
                        value = True
                    if refferal_result == 1 and survey_id in [6,7,8]:
                        value = False if refferal == 1 and survey_id == 5 else True
                        if survey_id == 7:
                            query=query.replace("@@survey_id","and s.id = '{0}'".format(int(survey_id)))
                            followup_query="""with a as ("""+query+""") select coalesce(sum(case when response->>'506'='54682' then 1 else 0 end),0) as ht from a"""
                            followup_result = get_result_query(followup_query)[0][0]
                            value = True if followup_result == 0 else False     
                    elif survey_id == 9:
                        query=query.replace("@@survey_id","and s.id = '{0}'".format(int(survey_id)))
                        call_management_query="""with a as ("""+query+""") select coalesce(sum(case when response->>'521'='119759' then 1 else 0 end),0) as ht from a"""
                        call_management_result = get_result_query(call_management_query)[0][0]
                        value = True if call_management_result == 0 else False 
                     
    elif survey_id == 3 and primary == 0:
        value = True
    elif survey_id == 10:
        value = True
    return value

        # object_lists=JsonAnswer.objects.raw(query)

# @register.simple_tag
# def check_menu_permission(user,menuname_value):

#     # 
#     # to check for the permission of user for the menu section
#     #
#     status = False
#     menuname = menuname_value
#     if user and menuname:
#         try:
#             user_obj = UserRoles.objects.get(user=user)
#         except:
#             user_obj = None
#         if user_obj:
#             roletypes = user_obj.role_type.all().values("id")
#             mlist = list(set(RoleConfig.objects.filter(active=2).filter(role__id__in=\
#                                             roletypes).values_list('menu__name',flat=True)))
#             new_mlist = [i.lower() for i in mlist]
#             if menuname in new_mlist:
#                 status = True
#     if user.is_superuser:
#         status = True
#     return status

### to get all menus which doesn't have parent ###
# @register.simple_tag
# def get_menu_list():
#     menu = Menus.objects.filter(active=2,parent=None)
#     return menu

# @register.simple_tag
# def display_user_theme(user):
#     userrole = UserRoles.objects.get_or_none(user = user)
#     userthemes = UserRolesTheme.objects.filter(user__user= user,active=2)
#     roles = RoleTypes.objects.filter(theme_display = True)
#     role_types = userrole.role_type.all() if userrole else []
#     common_roles = set(role_types) & set(roles)
#     status = True if common_roles else False
#     usertheme = userthemes[0] if userthemes else None
#     return status,userthemes,usertheme

# @register.simple_tag
# def get_side_menu(request):
#     side_menu = ''
#     if request:
#         side_menu = request.session.get('side_menu')
#     return side_menu

# @register.simple_tag
# def get_side_parent_menu(request):
#     side_menu = ''
#     if request:
#         parent_menu = request.session.get('parent_menu')
#     return parent_menu
    
# @register.simple_tag
# def get_second_parent_menu(request):
#     parent_side_menu = ''
#     if request:
#         parent_side_menu = request.session.get('parent_side_menu')
#     return parent_side_menu

# @register.simple_tag
# def get_theme_tagged_status(theme):
#     if ProjectTheme.objects.filter(project_theme = theme) or LineitemTheme.objects.filter(project_theme = theme):
#         status = False
#     else:
#         status = True
#     return status
    
# @register.simple_tag
# def get_user_name(request, u_id):
#     from masterdata.models import Boundary
#     name,boundary_name = '',''
#     try:
#         name = User.objects.get(id=int(u_id)).first_name
#         ur_obj = UserRoles.objects.get(user__id=int(u_id))
#         boundary_name = Boundary.objects.get(id=ur_obj.get_location_type()[0]).name if ur_obj.get_location_type()[0] else ''
#     except:
#         pass
#     return name,boundary_name

# @register.simple_tag
# def get_response_file(request, response_obj):
#     from survey.models import ResponseFiles
#     path = ''
#     rf = None
#     try:
#         rf = ResponseFiles.objects.get(question=response_obj.survey.questions().filter(qtype='F')[0], object_id=response_obj.id)
#     except:
#         rf = ResponseFiles.objects.filter(id=response_obj.id)
#     if rf:
#             path = 'http://sphoorthidev.mahiti.org/'+rf[0].response_image.name
#     return path

# @register.simple_tag
# def get_response_file_typeB(request, response_obj):
#     from survey.models import ResponseFiles
#     path = ''
#     rf = None
#     try:
#         rf = ResponseFiles.objects.get(question=response_obj.survey.questions().filter(qtype='F')[0], object_id=response_obj.id)
#     except:
#         pass
#     if rf:
#         path = 'http://sphoorthidev.mahiti.org/'+rf.response_image.name
#     return path

# @register.simple_tag
# def get_media_approve_status(response_obj):
#     from survey.models import SharedResponseUserRelation
#     status = ''
#     try:
#         rf = SharedResponseUserRelation.objects.get(response_id=response_obj.id)
#         status = True if rf.status == 1 or rf.status == 3 else False
#     except:
#         pass
#     status = False if status else True
#     return status

# @register.simple_tag
# def get_media_approve_reject_status(request, response_obj):
#     from survey.models import SharedResponseUserRelation
#     from programworkflow.models import WorkFlowLevelRoleUser
#     status = 0
#     try:
#         rf = SharedResponseUserRelation.objects.get(response_id=response_obj.id)
#         status = rf.status
#     except:
#         pass
#     wflr_obj = WorkFlowLevelRoleUser.objects.get_or_none(user=request.user, workflow_status__json_answer_id=response_obj.id)
#     if status == 1:
#         wf = WorkFlowLevelRoleUser.objects.filter(workflow_status__json_answer_id=response_obj.id).latest('id')
#         if wf.status == 1:
#             return status
#     if wflr_obj and wflr_obj.status == 4:
#         status = wflr_obj.status
#         if request.user.id in [844,1098]:
#             status = 3
#     return status

# @register.simple_tag
# def get_reject_status(response_obj):
#     from survey.models import SharedResponseUserRelation
#     reject_status = ''
#     try:
#         rf = SharedResponseUserRelation.objects.get(response_id=response_obj.id)
#         reject_status = True if rf.status == 2 else False
#     except:
#         pass
#    if rf.approve:
#        reject_status = False
#    elif reject_status:
#        reject_status = False
#    else:
#        reject_status = True
#     return reject_status

# @register.simple_tag
# def get_add_category_status(response_obj):
#     from django.contrib.contenttypes.models import ContentType
#     from survey.models import ResponseFiles
#     status = 'False'
#    if CommonRelation.objects.filter(content_type=ContentType.objects.get_for_model(response_obj),object_id=response_obj.id).exists():
#        status = 'False'
    # rf_obj = ResponseFiles.objects.get(id=response_obj.id)
    # if rf_obj.approve:
    #     status = 'True'
    # elif rf_obj.reject:
    #     status = 'True'
    # return status

# @register.simple_tag
# def get_communiction_obj(request,uuid):
#     from userroles.serializers import user_setup
#     obj=""
#     digital_content_url = user_setup().get('digital_content_url')
#     try:
#         http = urllib3.PoolManager()
#         encoded_body=json.dumps({'uuid':uuid})
#         response = http.request('POST',digital_content_url+'/api/get-replay-communication/', headers={'Content-Type':'application/json'},body=encoded_body)
#         obj=eval(response.data).get('content')
#     except:
#         pass
#     return obj

# @register.simple_tag
# def get_location_of_user(user_obj):
#     from masterdata.models import Boundary
#     try:
#         userrole_obj = UserRoles.objects.get(user=user_obj)
#         l = userrole_obj.get_location_type()[0]
#         boundary_name = Boundary.objects.get(id=l).name
#     except:
#         boundary_name = ''
#     return boundary_name
    
# @register.simple_tag
# def get_share_name_response(response_obj):
#     from survey.models import Choice
#     choice_obj = Choice.objects.get_or_none(id=response_obj.response.get('2849'))
#     name = ''
#     if choice_obj:
#         name = choice_obj.name
#     return name 

# @register.simple_tag
# def filter_level_data(data,level,index):
#     data_list = None
#     if index == 4: 
#         if data[level][3] == True:
#             parent_index = level-1
#             parent_id = data[parent_index][0] if parent_index >=0 else 0
#             data_list = data[level][index].get(str(parent_id))
#         else:
#             data_list = data[level][2]
#     else:
#         data_list = data[level][index]
#     if data_list:
#         return data_list
#     return []

# @register.simple_tag
# def now_timestamp():
#     from datetime import datetime as dt
#     now = dt.now()
#     return now.strftime('%Y%d%M%H%M%S%f') 

# @register.simple_tag
# def activities_count(ben_id):
#     print(ben_id)
#     ben_obj = BeneficiaryResponse.objects.get(id=ben_id)
#     return {'act_count':JsonAnswer.objects.filter(active=2,cluster__BeneficiaryResponse=ben_obj.creation_key).exclude(survey__id=321).count(), 'ben_count':BeneficiaryLink.objects.filter(active=2,object_id1=ben_id).count()}
