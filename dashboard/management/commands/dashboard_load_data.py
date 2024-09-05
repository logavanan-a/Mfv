import logging
from django.core.management.base import BaseCommand
import sys, traceback
import psycopg2
import json
from django.conf import settings
logger = logging.getLogger(__name__)
from django.db import connection
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from dashboard.models import DashboardSummaryLog


def generate_dashboard_data(year,month):
    result = None
    cursor = None
    conn = None
    try:
        db_name = settings.DATABASES['default'].get('NAME')
        hostname = settings.DATABASES['default'].get('HOST')
        username = settings.DATABASES['default'].get('USER')
        password = settings.DATABASES['default'].get('PASSWORD')
        conn = psycopg2.connect(database=db_name, user=username, password=password, host=hostname)
        conn.autocommit = True
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        cursor.execute(f"select dashboard_load_data({year},{month})")
        # result = cursor.fetchall()
        print('Dashboard Data Fetched Successfully')
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(error_stack)
    finally :
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result


class Command(BaseCommand):
    help = 'Custom command that accepts year and month as arguments'
    def add_arguments(self, parser):
        # Adding optional arguments for year and month with default values
        parser.add_argument('-y', '--year', type=int, help='Year (e.g., 2024)', default=None)
        parser.add_argument('-m', '--month', type=int, help='Month (e.g., 8)', default=None)
    def handle(self, *args, **options):
        year = options['year']
        month = options['month']
        key = 'dashboard_load_data'
        now = timezone.localtime(timezone.now())
        try:
            if year is not None and month is not None:
                generate_dashboard_data(year,month)
                logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                logdata.last_successful_update = now
                logdata.most_recent_update = now
                logdata.most_recent_update_status = 'Success'
                logdata.save()
            else:
                today = datetime.today()
                year = today.year
                month = today.month
                generate_dashboard_data(year,month)
                logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                logdata.last_successful_update = now
                logdata.most_recent_update = now
                logdata.most_recent_update_status = 'Success'
                logdata.save()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(
                exc_type, exc_value, exc_traceback))
            logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
            logdata.most_recent_update_status = 'Failed'
            logdata.most_recent_update = now
            logdata.error_details = str(error_stack)
            logdata.save()

