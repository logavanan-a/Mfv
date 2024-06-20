from django import template

register = template.Library()
# from userroles.serializers import *
# from userroles.models import *
# from budgetmanagement.models import BudgetLineitemConfig,BudgetLineitemPlanning,BudgetLineitemAchievments
# from projectmanagement.models import Project,Lineitem,ProjectDonor
from survey.models import Question,JsonAnswer,Choice,Language
# from masterdata.models import *
# from survey.views import user_setup
# from projectmanagement.models import LineitemTheme
# from projectmanagement.lineitems import get_lineitem_target

@register.simple_tag
def get_mobile_number(user):
    mobile = ''
    role = UserRoles.objects.get_or_none(user=user)
    mobile = role.mobile_number if role and role.mobile_number else ''
    return mobile

@register.simple_tag
def get_employe_type(user):
    employe_type = ''
    role = UserRoles.objects.get_or_none(user=user)
    employe_type = role.get_employe_type_display if role and role.employe_type else ''
    return employe_type

@register.simple_tag
def get_organization_unit_roletype(user):
    organization_unit= ''
    #roletype= ''
    obj = UserRoles.objects.get_or_none(user=user)
    roletype = obj.user_roles_names() if obj else ''
    organization_unit= obj.organization_unit.name if obj and obj.organization_unit_id else ''
    return organization_unit,roletype

    
@register.simple_tag
def get_target_amount(item,quarters):
    
    try:
        line_itemobj = BudgetLineitemConfig.objects.get(row_order = int(item.row_order),quarter = quarters,lineitem__id=item.lineitem.id,active=2)
    except:
        line_itemobj = BudgetLineitemConfig.objects.latest_one(row_order = int(item.row_order),quarter = quarters,lineitem__id=item.lineitem.id,active=2)
    return line_itemobjtarget_unit_type

@register.simple_tag
def lineitem_target_values (budget_lineitemobj,quarter_id,project_id,target_id):
    from budgetmanagement.views import get_budget_quarter_names
    plan_dict={}
    project = Project.objects.get(id=project_id)
    target_type = MasterLookUp.objects.get_or_none(id=int(target_id))
    quarter_list = get_budget_quarter_names(project.start_date,project.end_date)
    quarter = quarter_list[str(quarter_id)] if quarter_id else ''
    budgetobj = BudgetLineitemConfig.objects.get_or_none(id=int(budget_lineitemobj.id))
    budget_planning = BudgetLineitemPlanning.objects.get_or_none(budget_lineitem=budgetobj.id,quarter=quarter,target_type=target_type)
    achieved_obj = BudgetLineitemAchievments.objects.get_or_none(lineitem_planned=budget_planning,target_type=target_type)
    if achieved_obj:
        achieved = achieved_obj.achieved_value
        comment = achieved_obj.comments if achieved_obj.comments else ''
    else:
        achieved=''
        comment=''
    plan_dict.update({'achieved':achieved,
        'comment':comment})
    if budget_planning:
        plan_dict.update({'units':budgetobj.units,
        'unit_value':budget_planning.target_value if budget_planning.target_value else 0,
        'unit_type':budgetobj.unit_type,
        })
    else:
        plan_dict.update({'units':'','unit_value':'','unit_type':budgetobj.unit_type})
    
    return plan_dict
    
@register.simple_tag    
def target_unit_type(budgetobj):
    # fund_manage = user_setup().get('fund_management')
    budget_dict={}
    target = budgetobj.target_amount if budgetobj else 0
    budget_dict = {'target_value':target,
        'unit_type':budgetobj.unit_type if budgetobj else ''}
    return budget_dict

@register.simple_tag    
def get_theme_subtheme(lineitem):
    themes_obj=LineitemTheme.objects.filter(lineitem=lineitem)
    parent_list=[]
    child_list=[]
    
    for i in themes_obj:
        obj=i.project_theme
        if obj.parent == None:
            parent_list.append(obj.name)
        else:
            parent_list.append(obj.parent.name)
            child_list.append(obj.name)
    parent_theme = ','.join(parent_list)
    child_theme = ','.join(child_list)
    return {'parent':parent_theme,'child':child_theme}

@register.simple_tag
def get_theme_subtheme_new(lineitem):
    themes_obj=LineitemTheme.objects.filter(lineitem=lineitem)
    parent_list=[]
    child_list=[]
    a,b=[],[]
    for i in themes_obj:
        obj=i.project_theme
        if obj.parent == None:
            if i.section.id == 370:
                a.append(obj.name)
            elif i.section.id == 372:
                b.append(obj.name)
#            parent_list.append(obj.name)
        else:
            if i.section.id == 370:
                a.append(obj.parent.name)
            elif i.section.id == 372:
                b.append(obj.parent.name)
#            parent_list.append(obj.parent.name)
            child_list.append(obj.name)
#    parent_theme = ','.join(parent_list)
    a_theme = ','.join(a)
    b_theme = ','.join(b)
    child_theme = ','.join(child_list)
    return {'a':a_theme,'b':b_theme,'child':child_theme}

@register.simple_tag    
def get_quarters(year,project_id):
    from budgetmanagement.budget_admin import get_year_quarterlist
    quarter_list = get_year_quarterlist(year,project_id)
    return quarter_list
    
@register.simple_tag   
def get_unit_type(budget_lineitemobj):
    budgetobj = BudgetLineitemConfig.objects.get_or_none(id=int(budget_lineitemobj.id))
    unit_type = budgetobj.unit_type if budgetobj.unit_type else ''
    return unit_type

@register.simple_tag
def get_units_values(target_type,line_id):
    line_dict={
            'unit_type':'',
                'provide_units':'',
                'target_amount':'',
                'units':0,
        }
    if line_id :
        line_obj = Lineitem.objects.get_or_none(id=int(line_id))
        obj = BudgetLineitemConfig.objects.get_or_none(lineitem=line_obj,target_type=target_type)
        if obj :
            line_dict = {
                    'id':obj.id,
                    'unit_type':obj.unit_type.id if obj.unit_type else 0,
                    'provide_units':1 if obj.provide_units else 0,
                    'target_amount':obj.target_amount if obj.provide_units == False else obj.unit_value,
                    'units':obj.units or 0,
                     }
        
    return line_dict


@register.simple_tag
def get_incident_res(qut,response):
    try:
        qtobj = Question.objects.get(id=qut)
        if qtobj.qtype in ['S','R']:
            ans = Choice.objects.get(id=response.get(str(qut))).text
        else:
            ans = response.get(str(qut))
    except:
        ans = ''
    return ans


@register.simple_tag
def get_followup_res(response):
    try:
        ans = JsonAnswer.objects.get(id=response)
        qtobj = Question.objects.filter(block__survey=ans.survey).order_by('id')
        res = []
        for obj in qtobj:
            if obj.qtype in ['S','R']:
                cans = Choice.objects.get_or_none(id=ans.response.get(str(obj.id)))
                if cans:
                    cans = cans.text
                else:
                    cans = ''
                res.append(cans)
            else:
                res.append(ans.response.get(str(obj.id)))
    except:
        res = []
    return res


@register.simple_tag
def get_choice_txt(v):
    try:
        vv = Boundary.objects.get(id=v).name
    except:
        vv = ''
    return vv
    
@register.simple_tag
# def get_languages(request):
#     lang_display = user_setup().get('language_display')
#     count = Language.objects.filter(active=2).count()
#     if str(lang_display) == '0':
#         languages = False
#     else:
#         languages = True
#     return languages

@register.simple_tag
def get_donor_type_amount(lineitem):
    financial_amount = get_lineitem_target(lineitem,'Financial')
    physical_amount = get_lineitem_target(lineitem,'Physical')
    donor_type = {0: 'Primary', 1: 'Secondary'}[lineitem.donor.donor_type]
    return {'p_am':physical_amount , 'f_am':financial_amount,'donor_type':donor_type}
    
    
# @register.simple_tag
# def get_user_code(user):
#     if user_setup().get('user_display_code') == 2:
#         userrole = UserRoles.objects.get_or_none(user=user)
#         if userrole and not userrole.code :
#             code = user.id
#         else:
#             code = userrole.code
#     else:
#         code = ''
#     return code    

