from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.urls import reverse
from dashboard.models import MonthlyDashboard 
from mfv_mis.settings import DASHBOARD_SUBMISSION_DAY
from application_master.models import UserPartnerMapping,UserProjectMapping,PartnerMissionMapping

class CheckPreviousMonthDataSubmissionMiddleware:
    def __init__(self, get_response):
        # print(get_response.__dict__)
        self.get_response = get_response

    def __call__(self, request):
        # Get current date and calculate previous month
        current_date = datetime.now()
        validation_date = current_date.replace(day=DASHBOARD_SUBMISSION_DAY)
        previous_day = validation_date - timedelta(days=1)
        # month_year_need_to_check = str(previous_day.month)+""+str(previous_day.year)
        month_year_need_to_check = str(DASHBOARD_SUBMISSION_DAY)+""+str(validation_date.year)
        # Check if data has been submitted for the previous month
        user = request.user
        user_group_list = request.session.get('user_group_list',[])
        user_partner = request.session.get('user_partner_list_roshni',[])

        # import ipdb;ipdb.set_trace()
        if user.is_authenticated :
            url_list = request.path.split('/')
            if 1 in user_group_list and (('add-survey-form' in url_list) or ('edit-survey-form' in url_list)):
                submission_exists = MonthlyDashboard.objects.filter(
                    active=2,
                    partner_id__in = user_partner,
                    # month=month_year_need_to_check
                ).exists()
                # If data is not submitted, redirect to a specific page
                if not submission_exists:
                    request.session['show_submission_popup'] = {month_year_need_to_check:True}
                    

        response = self.get_response(request)
        return response
