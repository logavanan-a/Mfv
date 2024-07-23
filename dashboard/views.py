from django.shortcuts import render,HttpResponse
from django.db import connection
from dashboard.models import DashboardSummaryLog,MonthlyDashboard,Remarks,ACTIVE_CHOICES
from application_master.models import UserPartnerMapping,UserProjectMapping,PartnerMissionMapping
from datetime import datetime
from dateutil.relativedelta import relativedelta
from mis.models import *
from survey.views import get_pagination
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from send_mail.models import *
from send_mail.views import send_mail

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
    from survey.api_view import MonthlyDashboardData
    month = request.GET.get('month')
    submitted_on = request.GET.get('submitted_on')
    approval_status_id = request.GET.get('approval_status')
    approval_status = ACTIVE_CHOICES
    # import ipdb;ipdb.set_trace()
    user_partner = UserProjectMapping.objects.filter(active=2,user=request.user,project__application_type_id = 511).values_list('project__partner_mission_mapping__partner_id', flat=True)

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




@csrf_exempt
@login_required(login_url="/login/")
def dashboard_data_approval(request, id):
    monthly_data = MonthlyDashboard.objects.get(id=id)
    user_group = list(request.user.groups.all().values_list('id', flat=True))
    role_with_permisson_map = {1:4,2:2}
    if request.method == "POST":
        # 4 = Partner Admin
        # 1 = Partner Data Entry Operator
        # 2 = Project In-charge
        button = request.POST.get('label')
        approval = {'reject':-1,'approve':+1}
        monthly_data.current_status += approval.get(button)
        
        if 4 in user_group:
            monthly_data.current_status = 4 if button == 'reject' else monthly_data.current_status
            monthly_data.partner_admin = request.user
            monthly_data.partner_submitted = datetime.today()
        elif 2 in user_group:
            monthly_data.project_incharge = request.user
            monthly_data.project_incharge_submitted = datetime.today()

        monthly_data.save()
        if request.POST.get('remark'):
            group = request.user.groups.all()[0]
            remark_text = group.name + " - " + request.POST.get('remark')
            Remarks.objects.create(object_id=id,content_type_id=62,remark=remark_text,user=request.user)
        send_mail_with_template('Monthly Dashboard',['yuvaraj.kharvi@thesocialbytes.com'])
        return JsonResponse({'message': 'Updated successfully'})

    dashboard_data = {"No. of Children Screened":monthly_data.children_covered_count,"No. of Schools Covered":monthly_data.school_covered_count,"No. of Teachers Trained":monthly_data.teachers_train_count,"No. of Children Prescribed Spectacles":monthly_data.children_pres_count,"No. of Children Provided Spectacles":monthly_data.child_prov_spec_count,"No. of Children Advised to Continue with Same Glasses (PGP)":monthly_data.pgp_count,"No. of Children Referred to Hospital for Detailed Examination":monthly_data.children_reffered_count,"No. of Children Provided Spectacles at Hospital":monthly_data.child_prov_hos_count,"No. of Children Advised Surgery":monthly_data.children_adv_count,"No. of Children Provided Surgery":monthly_data.children_prov_sgy_count,"Spectacle Wearing Compliance After 3 Months":monthly_data.swc_count}

    month_obj = datetime.strptime(str(monthly_data.month), '%m%Y')
    remarks = Remarks.objects.filter(active=2,content_type_id=62,object_id=id).order_by('created')
    return render(request, "survey_forms/activity_submition_view.html", locals())




# mail passing function for approved/created the activities
def send_mail_with_template(template_name,to_users):

    # status = 'rejected' if approval_status in ['0',0] else 'approved'
    mail_template = MailTemplate.objects.get(active=2,template_name=template_name)
    to_ = ['yuvaraj.kharvi@thesocialbytes.com']
    # project_name = email_jsonobj[1].survey.get_activity_project()
    mail_subject = mail_template.subject#.format(email_jsonobj[1].survey.name, project_name.name if project_name else '',email_jsonobj[1].id)
    html_template = mail_template.content#.format(state_obj.label,email_jsonobj[0],email_jsonobj[1].survey.name,email_jsonobj[1].id,email_jsonobj[1].created.strftime("%Y-%m-%d %H:%M:%S"),email_jsonobj[1].survey.voucher_description or '-',f"{settings.INSTANCE_URL}/configuration/activity/{email_jsonobj[1].id}/",status,email_jsonobj[2])
    response = send_mail(to_,mail_subject,html_template,cc= ['yuvaraj.kharvi@thesocialbytes.com'])
    print(response,'response')
    mail_status = 3 if response['status'] == 200 else 1
    send_data_obj = MailData.objects.create(subject = mail_subject,content = html_template,mail_to = ';'.join([item for item in to_users if item]),
                                        priority = 1,mail_status = mail_status, send_attempt = 1,mail_cc="",mail_bcc="",
                                        template_name = mail_template,error_details = str(response) )

