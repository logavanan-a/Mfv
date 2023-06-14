from django.db import connection
from django.core.management.base import BaseCommand
import sys
import traceback
from dashboard.models import DashboardSummaryLog
from datetime import datetime
from django.utils import timezone

# import logging
import time

#Cron tab will set for every hour 20th and 40 th minutes
class Command(BaseCommand):
    help = 'Run command to refresh materialized views'

    def handle(self, *args, **options):
        """
        Executes the command to refresh materialized views.
        This command refreshes a list of materialized views by executing corresponding SQL queries.
        It updates the last successful update timestamp in the DashboardSummaryLog model for each view.
        In case of any errors during the refresh process, it logs the error details in the DashboardSummaryLog model.
        """
        import datetime
        # Define a dictionary of materialized views and their corresponding refresh queries
        refresh_query_list = {"mat_partner_mission_meta_view":"refresh materialized view mat_partner_mission_meta_view", 
                      "mat_target_view":"refresh materialized view mat_target_view", 
                      "mat_dashboard_achievement_view":"refresh materialized view mat_dashboard_achievement_view",
                      "mat_achievement_view":"refresh materialized view mat_achievement_view"}
        
        # Iterate over the refresh_query_list and execute the refresh queries
        for key,query in refresh_query_list.items():
            with connection.cursor() as cursor:
                try:
                    cursor.execute(query)
                    now = timezone.localtime(timezone.now())
                    logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                    logdata.last_successful_update = now
                    logdata.most_recent_update = now
                    logdata.most_recent_update_status = 'Success'
                    logdata.save()
                except Exception as e:
                    print('---------',e,'-------------')
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                        exc_type, exc_value, exc_traceback))
                    logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                    logdata.most_recent_update_status = 'Failed'
                    logdata.most_recent_update = timezone.localtime(timezone.now())
                    logdata.error_details = str(error_stack)
                    logdata.save()
            time.sleep(1)
