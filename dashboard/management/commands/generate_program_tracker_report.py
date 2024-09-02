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


def generate_donor_data(year,q_year):
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
        cursor.execute(f"select load_donor_quarterly_report({year},{q_year})")
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
        parser.add_argument('-q', '--quarterly', type=int, help='Month (e.g., 1,2,3,4)', default=None)
    def handle(self, *args, **options):
        year = options['year']
        quarter = options['quarterly']
        key = 'program_tracker_data'
        now = timezone.localtime(timezone.now())
        try:
            if year is not None and quarter is not None:
                generate_donor_data(year,quarter)
                print(f'program_tracker Report Data Fetched Successfully --{year} - {quarter}')
                logdata, created = DashboardSummaryLog.objects.get_or_create(log_key=key)
                logdata.last_successful_update = now
                logdata.most_recent_update = now
                logdata.most_recent_update_status = 'Success'
                logdata.save()
            else:
                today = datetime.today()
                year = today.year
                month = today.month
                if month in (7,8,9):
                    generate_donor_data(year,1)
                    print('Donor Report Data Fetched Successfully --1st Quarter')
                elif month in (10,11,12):
                    generate_donor_data(year,2)
                    print('Donor Report Data Fetched Successfully --2nd Quarter')
                elif month in (1,2,3):
                    generate_donor_data(year,3)
                    print('Donor Report Data Fetched Successfully --3rd Quarter')
                elif month in (4,5,6):
                    generate_donor_data(year,4)
                    print('Donor Report Data Fetched Successfully --4th Quarter')
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
            

