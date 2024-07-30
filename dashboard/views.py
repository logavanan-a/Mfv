from django.shortcuts import render,HttpResponse
from django.db import connection
from dashboard.models import DashboardSummaryLog,MonthlyDashboard,Remarks,STATUS_CHOICES,ArrayField
from application_master.models import UserPartnerMapping,UserProjectMapping,PartnerMissionMapping
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta
from mis.models import *
from survey.views import get_pagination,JsonAnswer
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from send_mail.models import *
from send_mail.views import send_mail
from django.db.models import Case, Value, When, Q , Sum
from mfv_mis.settings import DASHBOARD_SUBMISSION_DAY
from uuid import uuid4
from survey.api_view import MonthlyDashboardData
import sys, traceback
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def dashboard(request):
    """
    View function for the dashboard page.

    This view handles the rendering of the dashboard page and performs necessary operations
    such as executing a database query, fetching data, and passing it to the template.

    """
    heading = "Dashboard"
    start_month =  request.POST.get('start_filter','') 
    end_month = request.POST.get('end_filter','')
    query = build_query(request)
    # execute query 
    # parse the 1 row returned from the query and assign values to the dashboard placeholders in blade
    # add logic to hide the mission / programs based on the user type and data visibility
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    partner = request.POST.get('partner') if(request.POST.get('partner') != 'None') else None
    partners = int(partner) if partner not in [None, 'None', ''] else None

    partner_objs = Partner.objects.filter(active=2,id__in=request.session['user_partner_list']).order_by('name')
    dash_summary = DashboardSummaryLog.objects.filter(log_key="mat_partner_mission_meta_view").first()
    last_updated_on = ''
    if dash_summary and dash_summary.last_successful_update:
        last_updated_on = datetime.strftime(dash_summary.last_successful_update,'%d-%m-%Y %-I%M %p')
    return render(request, 'dashboard/dashboard.html', locals())

def build_query(request):
    """
    Build and return the SQL query based on the request parameters.

    This function constructs a SQL query using the request parameters, such as start month,
    end month, and user filters. It replaces placeholders in the base query string with
    the corresponding values.
    """
    start_month =  request.POST.get('start_filter','')
    end_month = request.POST.get('end_filter','')
    partner = request.POST.get('partner') if(request.POST.get('partner') != 'None') else None
   
    start_date,end_date,start_month_condition,end_month_condition='','','',''
    if start_month:
        start_date = start_month + "-01"
        start_month_condition='and ach.task_month >= ' + start_month.replace('-', '')
    if end_month:
        end_date = end_month + "-01"
        end_date = datetime.strptime(end_date,'%Y-%m-%d')
        end_date = end_date + relativedelta('1 months')
        end_date = datetime.strftime(end_date,'%Y-%m-%d')
        end_month_condition='and ach.task_month <= ' + end_month.replace('-', '')

    logged_in_user_id = request.user.id#request_get user_id

    query="""select coalesce(jyot_vcs.vcs_count,0) as jyot_vcs_count, a.* from (select sum(case when key in ('total_33','total_296') then value else 0 end) as jyot_eye_screening,
            sum(case when key in ('total_40','total_346') then value else 0 end) as jyot_spectacles_dispensed,
            sum(case when key in ('total_301','total_46','total_292','total_304') then value else 0 end) as jyot_surgeries,
            0 as jyot_average_opd_vc,
            sum(case when key in ('total_40') then value else 0 end) as jyot_spectacles_conversion_vc_numerator,
            sum(case when key in ('total_39') then value else 0 end) as jyot_spectacles_conversion_vc_denominator,
            0 as jyot_avg_spec_transaction_value_vc_numerator,
            0 as jyot_avg_spec_transaction_value_vc_denominator,
            sum(case when key in ('total_121','total_221','total_122','total_222','total_223') then value else 0 end) as nayan_neonates_screened_rop,
            sum(case when key in ('total_224','total_225') then value else 0 end) as nayan_children_rop_positive,
            sum(case when key in ('total_229','total_230','total_232','total_231') then value else 0 end) as nayan_num_treatments_done,
            0 as jeevan_child_enrolled,
            sum(case when key in ('total_16') then value else 0 end) as roshni_children_screened,
            sum(case when key in ('total_132') then value else 0 end) as roshni_spectacles_dispensed,
            sum(case when key in ('total_1') then value else 0 end) as disha_screening,
            sum(case when key in ('total_2') then value else 0 end) as disha_spectacles_dispensed,
            0 as saksham_aop_completed_training,
            sum(case when key in ('total_284') then value else 0 end) as saksham_aop_in_training,
            0 as netra_cataract_surgeries,
            sum(case when key in ('total_112','total_273','total_264') then value else 0 end) as base_screening,
            sum(case when key in ('total_274','total_265','total_113') then value else 0 end) as base_cataract_surgeries,
            sum(case when key in ('total_281','total_272','total_263') then value else 0 end) as base_other_surgeries,
            (case when coalesce(sum(case when key in ('total_33','total_296') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_40','total_346') then value else 0 end) * 100/sum(case when key in ('total_33','total_296') then value else 0 end)::numeric,0) end)::integer as jyot_spectacles_dispensed_percentage,
            (case when coalesce(sum(case when key in ('total_33','total_296') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_301','total_46','total_292','total_304') then value else 0 end) * 100/sum(case when key in ('total_33','total_296') then value else 0 end)::numeric,0) end)::integer as jyot_surgeries_percentage,
            (case when coalesce(sum(case when key in ('total_16') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_132') then value else 0 end) * 100/sum(case when key in ('total_16') then value else 0 end)::numeric,0) end)::integer as roshni_spectacles_dispensed_percentage,
            (case when coalesce(sum(case when key in ('total_1') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_2') then value else 0 end) * 100/sum(case when key in ('total_1') then value else 0 end)::numeric,0) end)::integer as disha_spectacles_dispensed_percentage,
            (case when coalesce(sum(case when key in ('total_112','total_273','total_264') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_274','total_265','total_113') then value else 0 end) * 100/sum(case when key in ('total_112','total_273','total_264') then value else 0 end)::numeric,0) end)::integer as base_cataract_surgeries_percentage,
            (case when coalesce(sum(case when key in ('total_112','total_273','total_264') then value else 0 end),0) = 0 then 0::numeric else round(sum(case when key in ('total_281','total_272','total_263') then value else 0 end) * 100/sum(case when key in ('total_112','total_273','total_264') then value else 0 end)::numeric,0) end)::integer as base_other_surgeries_percentage
            from mat_dashboard_achievement_view as ach
            where 1=1 @@fvalue_start_month @@fvalue_end_month @@user_project_filter @@user_partner_filter @@partnerfilter
            ) as a
            left outer join (select mission_id, count(distinct project_id) as vcs_count
            from mat_partner_mission_meta_view
            where mission_id = 5 @@fvalue_start_date @@fvalue_end_date
            @@user_project_filter @@user_partner_filter @@partnerfilter
            group by mission_id
            ) as jyot_vcs on true"""

    user_partner_filter_cond = ""
    user_project_filter_cond = ""

    if request.user.is_superuser:
        user_project_filter_cond=''
    elif UserPartnerMapping.objects.filter(user=request.user).exists() :#and user is partner_level_user then 
        user_partner_filter_cond = """ and project_id in (select distinct project_id 
                                                    from mat_partner_mission_meta_view 
                                                    where partner_id in (select partner_id 
                                                            from application_master_userpartnermapping 
                                                            where user_id = """ + str(logged_in_user_id) +"""
                                                    )
                                        ) """
    elif UserProjectMapping.objects.filter(user=request.user).exists():#user is project_level_user then 
        user_project_filter_cond = """ and project_id in (select project_id 
                                            from application_master_userprojectmapping 
                                            where user_id = """ + str(logged_in_user_id) + """)"""
    
    end_date_condition=''
    if start_date != '':
        end_date_condition="and (project_end_date is null or project_end_date >= '" + start_date +"')" 

    start_date_condition=''
    if end_date != '':
        start_date_condition="and project_start_date < '" + end_date +"'" 

    partner_cond = ''
    if partner :
        partner_cond = """ and project_id in (select distinct project_id 
                                                    from mat_partner_mission_meta_view 
                                                    where partner_id = """ + partner +"""
                                                    ) """

    query = query.replace("@@user_partner_filter",user_partner_filter_cond) 
    query = query.replace("@@user_project_filter",user_project_filter_cond)
    query = query.replace("@@fvalue_start_date",start_date_condition) #should be of format 2022-01-25
    query = query.replace("@@fvalue_end_date",end_date_condition) #should be of format 2022-01-25
    query = query.replace("@@fvalue_start_month",start_month_condition) #should be of format 202201
    query = query.replace("@@fvalue_end_month",end_month_condition) #should be of format 202201
    query = query.replace("@@partnerfilter",partner_cond)
    return query



@login_required(login_url="/login/")
def monthly_dashboard_list(request):
    month = request.GET.get('month')
    submitted_on = request.GET.get('submitted_on')
    approval_status_id = request.GET.get('approval_status')
    approval_status = STATUS_CHOICES

    # user_partner = UserProjectMapping.objects.filter(active=2,user=request.user,project__application_type_id = 511).values_list('project__partner_mission_mapping__partner_id', flat=True)
    user_partner = request.session['user_partner_list_roshni']

    object_list = MonthlyDashboard.objects.filter(active=2,partner__in=user_partner).order_by('-modified').select_related('partner','project_incharge','partner_admin','submitted_by')
    if month:
        month_int = ''.join(month.split('-')[::-1])
        object_list = object_list.filter(month = month_int)
    
    if submitted_on:
        object_list = object_list.filter(created__date = submitted_on)
    
    if approval_status_id:
        object_list = object_list.filter(current_status = approval_status_id)

    object_list = get_pagination(request, object_list)
    return render(request, "survey_forms/activity_list.html", locals())



from types import SimpleNamespace
from django.test import RequestFactory
from django.http import HttpRequest, JsonResponse
import json
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

@csrf_exempt
@login_required(login_url="/login/")
def dashboard_data_approval(request, id):
    from survey.api_views_version1 import submitted_record_mails
    try:
        monthly_data = MonthlyDashboard.objects.get(id=id)
        month_obj = datetime.strptime(str(monthly_data.month), '%m%Y')
    except:
        current_date = datetime.now()
        month_obj,end_of_previous_month=get_first_and_last_date_of_month(current_date.year,DASHBOARD_SUBMISSION_DAY)
        # first_day_of_current_month = current_date.replace(day=1)
        # first_day_of_current_month = current_date.replace(month=DASHBOARD_SUBMISSION_DAY)
        # month_obj = first_day_of_current_month - timedelta(days=1)
        # month_obj = first_day_of_current_month.replace(day=1)
        # start_of_previous_month = month_obj.replace(day=1)
        # print(start_of_previous_month.date(),month_obj.date())
        monthly_data_queryset = JsonAnswer.objects.values(
            'cluster__BeneficiaryResponse'
        ).filter(
            active=2,
            survey_id__in=[6, 8, 5, 4, 3, 10],
            created__date__range=[month_obj,end_of_previous_month]
        ).annotate(
            primary_screening_done=Sum(
                Case(
                    When(
                        (~Q(response__contains={"407": ""})),
                        survey_id=3,
                        response__has_key="407",
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            secondary_screening_done=Sum(
                Case(
                    When(
                        (~Q(response__contains={"405": ""})),
                        survey_id=4,
                        response__has_key="405",
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            teachers_training_done=Sum(
                Case(
                    When(
                        survey_id=10,
                        response__contains={"393": "262"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            teachers_training_notdone=Sum(
                Case(
                    When(
                        survey_id=10,
                        response__contains={"393": "263"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            rx_spec=Sum(
                Case(
                    When(
                        survey_id=4,
                        response__contains={"282": "176"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            prov_spec=Sum(
                Case(
                    When(
                        (~Q(response__contains={"355": ""})),
                        survey_id=8,
                        response__has_key="355",
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            advc_same_spec=Sum(
                Case(
                    When(
                        survey_id=4,
                        response__contains={"281": "173"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            ref_hosp_exam=Sum(
                Case(
                    When(
                        survey_id=4,
                        response__contains={"284": "180"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            prov_spec_hosp=Sum(
                Case(
                    When(
                        survey_id=4,
                        response__contains={"283": "179"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            advc_surgery=Sum(
                Case(
                    When(
                        survey_id=5,
                        response__contains={"343": "200"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            prov_surgery=Sum(
                Case(
                    When(
                        survey_id=6,
                        response__contains={"345": "204"},
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            swc_3months=Sum(
                Case(
                    When(
                        Q(response__contains={"356": "222"}) | Q(response__contains={"356": "224"}),
                        survey_id=8,
                        then=Value(1)
                    ),
                    default=Value(0),
                )
            ),
            combined_screening_done=Case(
                When(
                    Q(primary_screening_done__gte=1) & Q(secondary_screening_done__gte=1),
                    then=Value(1)
                ),
                default=Value(0),
            ),
            is_school=Case(
                When(survey__config__0__object_id_1='3', then=Value(1)),
                default=Value(0),
            ),
            is_student=Case(
                When(survey__config__0__object_id_1='2', then=Value(1)),
                default=Value(0),
            ),
            school_covered=Case(
                When(
                    Q(is_school=1) & Q(Q(combined_screening_done__gte=1) | Q(teachers_training_done__gte=1) | Q(teachers_training_notdone__gte=1)),
                    then=Value(1)
                ),
                default=Value(0),
            )
        )
        monthly_data_dict = monthly_data_queryset.aggregate(
            children_covered_count=Sum('combined_screening_done'),
            # sum_primary_screening_done=Sum('primary_screening_done'),
            # sum_secondary_screening_done=Sum('secondary_screening_done'),
            teachers_train_count=Sum('teachers_training_done'),
            # sum_teachers_training_notdone=Sum('teachers_training_notdone'),
            children_pres_count=Sum('rx_spec'),
            child_prov_spec_count=Sum('prov_spec'),
            pgp_count=Sum('advc_same_spec'),
            children_reffered_count=Sum('ref_hosp_exam'),
            child_prov_hos_count=Sum('prov_spec_hosp'),
            children_adv_count=Sum('advc_surgery'),
            children_prov_sgy_count=Sum('prov_surgery'),
            swc_count=Sum('swc_3months'),
            school_covered_count=Sum('school_covered')
        )

        # Convert the queryset to a list of SimpleNamespace objects
        monthly_data = SimpleNamespace(**monthly_data_dict)
        
    
    # mapping for table of indicator counts
    dashboard_data = {"No. of Children Screened":monthly_data.children_covered_count,"No. of Schools Covered":monthly_data.school_covered_count,"No. of Teachers Trained":monthly_data.teachers_train_count,"No. of Children Prescribed Spectacles":monthly_data.children_pres_count,"No. of Children Provided Spectacles":monthly_data.child_prov_spec_count,"No. of Children Advised to Continue with Same Glasses (PGP)":monthly_data.pgp_count,"No. of Children Referred to Hospital for Detailed Examination":monthly_data.children_reffered_count,"No. of Children Provided Spectacles at Hospital":monthly_data.child_prov_hos_count,"No. of Children Advised Surgery":monthly_data.children_adv_count,"No. of Children Provided Surgery":monthly_data.children_prov_sgy_count,"Spectacle Wearing Compliance After 3 Months":monthly_data.swc_count}


    user_group = request.session['user_group_list']
    
    # if record status have the permission of group to action {status:role id (group)}
    role_with_permisson_map = {1:4,2:2,3:3}

    if request.method == "POST":
        # 4 = Partner Admin
        # 1 = Partner Data Entry Operator
        # 2 = Project In-charge
        # 3 = MFV Admin
        button = request.POST.get('label')
        approval = {'reject':-1,'approve':+1}
        partner_list = request.session.get('user_partner_list')
        if id == 'new':
            array_fields = [
                field.name for field in MonthlyDashboard._meta.get_fields()
                if isinstance(field, ArrayField)
            ]
            for field in array_fields:
                monthly_data_dict[field] = []

            month_field = month_obj.strftime('%m%Y')

            # Preprocess the dictionary to replace None with 0
            preprocessed_dict = {k: (0 if v is None else v) for k, v in monthly_data_dict.items()}

            monthly_data, _ = MonthlyDashboard.objects.update_or_create(month = month_field,creation_key = datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid4()),partner_id=partner_list[0],submitted_by = request.user,defaults=preprocessed_dict)
            
            # removing the session true for this month
            del request.session['show_submission_popup']

        monthly_data.current_status += approval.get(button)
        
        if 4 in user_group:
            # if only partner admin rejected means it will be 5 (rejected)
            monthly_data.current_status = 5 if button == 'reject' else monthly_data.current_status
            monthly_data.partner_admin = request.user
            monthly_data.partner_submitted = datetime.today()
        elif 2 in user_group:
            monthly_data.project_incharge = request.user
            monthly_data.project_incharge_submitted = datetime.today()

        monthly_data.save()
        if request.POST.get('remark'):
            group = request.user.groups.all()[0]
            remark_text = f"{request.user.username} ({group.name})  -  {request.POST.get('remark')}"
            Remarks.objects.create(object_id=monthly_data.id,content_type_id=62,remark=remark_text,user=request.user)

        # sending email for respected role users
        try:
            send_mail_with_template(request,monthly_data,dashboard_data)
            message = 'Updated successfully'
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logger.error(error_stack)
            message = f"Error while sending mail. Please contact your system administrator. {str(e)}"
        return JsonResponse({'message': message})

    
    remarks = Remarks.objects.filter(active=2,content_type_id=62,object_id=monthly_data.id).order_by('created')
    return render(request, "survey_forms/activity_submition_view.html", locals())

# mail passing function for approved/created the activities
def send_mail_with_template(request,monthly_data,dashboard_data):
    user_group = request.session['user_group_list'][0]
    partner_list = request.session['user_partner_list_roshni']
    button = request.POST.get('label')
    # key is from role id , if role rejected means which role need to go if approved then which role need to go
    role_with_mail = {
        4:{'reject':[1],'approve':[2]},
        2:{'reject':[4],'approve':[1,4]},
        # 3:{'reject':2},
    }
    to_role = role_with_mail.get(user_group).get(button)
    if to_role:
        template_name = f"{user_group}->{','.join(map(str,to_role))}"
        mail_template = MailTemplate.objects.get(active=2,template_name=template_name)
        to_email_username = get_next_role_user(partner_list,to_role)

        to_users_and_email = {}
        for user in to_email_username:
            name = user[2]
            if user[0] or user[1]:
                name = f"{user[0] or ''} {user[1] or ''} ({user[2]})"
            to_users_and_email[name] = user[3]
        # import ipdb;ipdb.set_trace()
        users_name, to_users_emails = zip(*to_users_and_email.items())
        from_username = f"{request.user.get_full_name()} ({request.user.username})" if request.user.get_full_name() else request.user.username

        if users_name and to_users_emails:
            table_html = render_to_string('mailer/table_for_dashboard_data.html', {'dashboard_data': dashboard_data})
            join_usersname = ' and '.join(users_name) if len(users_name) > 1 else users_name[0]
            
            month_obj = datetime.strptime(str(monthly_data.month), '%m%Y')
            partner_name = monthly_data.partner.name
            mail_subject = mail_template.subject.format(partner_name=partner_name, month_year=month_obj.strftime('%B %Y'))
            html_template = mail_template.content.format(partner_name=partner_name,month_year=month_obj.strftime('%B %Y'),to_username=join_usersname,from_username=from_username)
            table_html = convert_safe_text(table_html)
            html_template = html_template.replace('@@dashboard_content',table_html)
            html_template = html_template.replace('@@remark',request.POST.get('remark',''))
            response = send_mail(set(to_users_emails),mail_subject,html_template)
            print(response,'response')
            mail_status = 3 if response['status'] == 200 else 1
            send_data_obj = MailData.objects.create(subject = mail_subject,content = html_template,mail_to = ';'.join([item for item in to_users_emails if item]),
                                                priority = 1,mail_status = mail_status, send_attempt = 1,mail_cc="",mail_bcc="",
                                                template_name = mail_template,error_details = str(response) )

def get_next_role_user(partner,to_role):
    email_username = list(UserProjectMapping.objects.filter(active=2,project__partner_mission_mapping__partner_id__in=partner,project__application_type_id=511,user__groups__id__in=to_role).values_list('user__first_name','user__last_name','user__username','user__email').exclude(user__email__isnull=True).exclude(user__email__exact='').distinct())
    return email_username

def convert_safe_text(content):
	try:
		if type(content) != str:
			content = str(content)
	except:
		content = str(content.encode("utf8"))
	return content




def get_first_and_last_date_of_month(year, month):
    # Ensure month is within the valid range
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")

    # First date of the month
    first_date = datetime(year, month, 1)
    
    # Last date of the month
    # Compute the first day of the next month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    # Subtract one day from the first day of the next month
    last_date = next_month - timedelta(days=1)

    return first_date, last_date
