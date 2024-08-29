from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime,timedelta
from send_mail.models import MailData
from send_mail.views import send_mail
import sys, traceback
import logging
import os
from survey.models import JsonAnswer
from django.db.models import Q,Count
from django.template.loader import render_to_string
from collections import Counter


class Command(BaseCommand):

    """ Command To update question in csv format."""
    
    def handle(self,*args, **options):
        try:
            mail_content,table_data={},{}
            yesterday = datetime.now() - timedelta(1)
            filename = f'{settings.MEDIA_DIR}/logSync/{yesterday.year}/{yesterday.month:02d}/{yesterday.day:02d}/SyncLog-{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}.txt'
            #checking the file is exists or not
            isExist = os.path.exists(filename)
            if isExist:
                with open(filename, "r") as f:
                    content = f.read()

                blank_push = content.count('"pushInput": []')
                print(f"Total number of empty pushInput - {blank_push}")

                total_push = content.count('"pushInput"')
                res=total_push-blank_push
                print(f"Total number of NON EMPTY pushInput - {res}")

                non_error = content.count('error_msg": ""')
                total_error = content.count('error_msg')
                error_count=total_error-non_error
                print(f"Total number of ERROR input - {error_count}")

                result=[]
                for word in content.splitlines():
                    if 'error_msg' in word and word not in result: 
                        result.append(word.strip())
                print(f"Error List - {result}")
                
                # Remove the outer quotes and split by comma, then take the second part
                error_msgs_cleaned = [msg.split('"error_msg": ')[1].strip('"') for msg in result]

                # Count occurrences of each error message
                result = dict(Counter(error_msgs_cleaned))

                mail_content['filename']=f'<a href="{settings.HOST_URL}/media/logSync/{yesterday.year}/{yesterday.month:02d}/{yesterday.day:02d}/SyncLog-{yesterday.year}-{yesterday.month:02d}-{yesterday.day:02d}.txt" target="_blank">{filename}</a>'
                mail_content['blank_push']=blank_push
                mail_content['res']=res
                mail_content['error_count']=error_count
                mail_content['result']=result

                try:
                    mail_to = settings.APP_EMAIL_SETTINGS['TEST_MAIL_LIST']
                    mail_cc = settings.ACTIVITY_MAIL_CC
                    mail_subject = f'ROSHNI - Error Log ({settings.HOST_URL})'
                    # mail_content = f" File Path - {filename}<br>Total number of empty pushInput - {blank_push} <br> Total number of NON EMPTY pushInput - {res} <br> Total number of ERROR input - {error_count} <br> Error List - {result}"
                    response = send_mail(mail_to,mail_subject,mail_content,'mailer/sync_history_template.html',cc=mail_cc)
                    print(response,'response')
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
                    print(error_stack)
            else:
                print(f"File Not Found - {filename}")
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print(error_stack)