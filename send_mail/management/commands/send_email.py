from __future__ import unicode_literals
from django.core.management.base import BaseCommand
import datetime 
from send_mail.models import MailData
from send_mail.views import send_mail
from django.conf import settings
import sys, traceback
import logging;


def sendmail():
    batch_size = settings.APP_EMAIL_SETTINGS['BATCH_SIZE']
    #mail status: choices  1-new, 2-makedToSend, 3-Sent, 4-Failed ,5 -Ignored
    mail_obj = MailData.objects.filter(mail_status = 1).order_by('priority','-send_attempt','created')[:batch_size]
    max_attempts = settings.APP_EMAIL_SETTINGS['MAX_ATTEMPTS']
    for x in mail_obj:
        try:
            mail_to = x.mail_to.split(";")
            cc      = x.mail_cc.split(";")
            bcc     = x.mail_bcc.split(";")
            #If test mode, check if mail_to id in TEST_MAIL_LIST
            # if mail_to in list, send the email otherwise don't send email and set status to ignored
            x.mail_status = 2
            if settings.APP_EMAIL_SETTINGS['MODE'] == 'TEST':
                test_mail_list = set(settings.APP_EMAIL_SETTINGS['TEST_MAIL_LIST'])
                mail_to = [item for item in mail_to if item in test_mail_list]
                cc = [item for item in cc if item in test_mail_list]
                bcc = [item for item in bcc if item in test_mail_list]
                if len(mail_to) == 0 and len(cc)== 0 and len(bcc) == 0:
                    x.mail_status = 5
                    x.error_details = 'Ignored because MODE is TEST and email ID not in TEST_MAIL_LIST'  
            #if not test mode and 
            if x.mail_status == 2:
                mail_subject = x.subject
                mail_content = x.content
                mail_template = x.template_name.html_template
                response = send_mail(mail_to,mail_subject,mail_content,mail_template,cc=cc,bcc=bcc,filepaths=x.file_paths)
                x.send_attempt = int(x.send_attempt)+1
                x.time_last_attempt = datetime.datetime.now()
                x.mode = settings.APP_EMAIL_SETTINGS['MODE']
                if response['status'] == 200:
                    x.mail_status = 3
                elif x.send_attempt >= max_attempts:
                    x.error_details = str(response)
                    x.mail_status = 4
                else:
                    x.error_details = str(response)
                    x.mail_status = 1
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            x.error_details = str(error_stack)
        x.save()                

    
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            sendmail()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_stack = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logging.error(str(error_stack))
            print(str(error_stack))