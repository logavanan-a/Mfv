from django.db import connection
from django.core.management.base import BaseCommand
import sys
import traceback
from dashboard.models import DashboardSummaryLog
from datetime import datetime
# import logging
import time


class Command(BaseCommand):
    help = 'Run command to refresh materialized views concurrently'

    def handle(self, *args, **options):
        import datetime
        # logger = logging.getLogger('dashboard')
        refresh_query_list = {"mat_partner_mission_meta_view":"refresh materialized view concurrently mat_partner_mission_meta_view", 
                      "mat_target_view":"refresh materialized view concurrently mat_target_view", 
                      "mat_dashboard_achievement_view":"refresh materialized view concurrently mat_dashboard_achievement_view"}
        for key,query in refresh_query_list.items():
            with connection.cursor() as cursor:
                try:
                    cursor.execute(query)
                    # cursor.fetchall()
                    now = datetime.datetime.now()
                    logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                    logdata.last_successful_update = now
                    logdata.most_recent_update = now
                    logdata.most_recent_update_status = 'Success'
                    logdata.save()
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(
                        exc_type, exc_value, exc_traceback))
                    # logger.error("error in :" + str(e))
                    # logger.error(error_stack)
                    logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                    logdata.most_recent_update_status = 'Failed'
                    logdata.most_recent_update = datetime.datetime.now()
                    logdata.error_details = str(error_stack)
                    logdata.save()
            time.sleep(1)
