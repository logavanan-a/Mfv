from django.shortcuts import render
from django.db import connection
from dashboard.models import DashboardSummaryLog
from application_master.models import UserPartnerMapping,UserProjectMapping,PartnerMissionMapping
from django.shortcuts import render
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
            where 1=1 @@fvalue_start_month @@fvalue_end_month @@user_project_filter @@user_partner_filter
            ) as a
            left outer join (select mission_id, count(distinct project_id) as vcs_count
            from mat_partner_mission_meta_view
            where mission_id = 5 @@fvalue_start_date @@fvalue_end_date
            @@user_project_filter @@user_partner_filter
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


    query = query.replace("@@user_partner_filter",user_partner_filter_cond) 
    query = query.replace("@@user_project_filter",user_project_filter_cond)
    query = query.replace("@@fvalue_start_date",start_date_condition) #should be of format 2022-01-25
    query = query.replace("@@fvalue_end_date",end_date_condition) #should be of format 2022-01-25
    query = query.replace("@@fvalue_start_month",start_month_condition) #should be of format 202201
    query = query.replace("@@fvalue_end_month",end_month_condition) #should be of format 202201
    return query
