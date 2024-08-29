from mfv_mis.settings import ACTIVITY_MAIL_RECIEVER, ACTIVITY_MAIL_CC,ACTIVITY_MAIL_BCC
from survey.models import *
from django.template import loader
from django.core.mail import send_mail
from datetime import datetime, timedelta
from send_mail.models import *
from django.db.models import Count
# import datetime



def survey_responses():
    today = datetime.now().date()
    prev_day = today-timedelta(days=1)
    prev_date = prev_day.strftime("%Y-%m-%d")
    tod_date = today.strftime("%Y-%m-%d")
    date_fmt = prev_day.strftime("%d-%m-%Y")
    month_first = today.replace(day=1)
    
    start = (datetime.now() - timedelta(days=datetime.now().weekday())).date()
    end_week = start + timedelta(days=6)

    surveys = Survey.objects.filter(active=2).order_by("name")
    main_dic = {}
    beneficiary_ids = list(Survey.objects.filter(active=2,survey_type=0).order_by("id").values_list('id',flat=True))
    for i in surveys:
        main_dic.update({i.id: {"name":i.name, "y_c":0,"y_m":0, "w_c":0, "w_m":0, "m_c":0, "m_m":0, "t":0}})

    total_resp = JsonAnswer.objects.filter(survey__active=2,created__lte = prev_date+" 23:59:59").values('survey_id').annotate(total_count=Count('survey_id'))
    for i in total_resp:
        main_dic.get(i.get("survey_id")).update({"t":i.get("total_count")})

    yesterday_resp_created = JsonAnswer.objects.filter(survey__active=2,created__range=(prev_date+" 00:00:00",prev_date+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    yesterday_resp_modified = JsonAnswer.objects.filter(survey__active=2,modified__range=(prev_date+" 00:00:00",prev_date+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    for i in yesterday_resp_created:
        main_dic.get(i.get("survey_id")).update({"y_c":i.get("total_count")})
    for i in yesterday_resp_modified:
        main_dic.get(i.get("survey_id")).update({"y_m":i.get("total_count")})

    weekly_resp_created = JsonAnswer.objects.filter(survey__active=2,created__range=(str(start)+" 00:00:00",str(end_week)+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    weekly_resp_modified = JsonAnswer.objects.filter(survey__active=2,modified__range=(str(start)+" 00:00:00",str(end_week)+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    for i in weekly_resp_created:
        main_dic.get(i.get("survey_id")).update({"w_c":i.get("total_count")})
    for i in weekly_resp_modified:
        main_dic.get(i.get("survey_id")).update({"w_m":i.get("total_count")})

    monthly_resp_created = JsonAnswer.objects.filter(survey__active=2,created__range=(str(month_first)+" 00:00:00",prev_date+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    monthly_resp_modified = JsonAnswer.objects.filter(survey__active=2,modified__range=(str(month_first)+" 00:00:00",prev_date+" 23:59:59")).values('survey_id').annotate(total_count=Count('survey_id'))
    for i in monthly_resp_created:
        main_dic.get(i.get("survey_id")).update({"m_c":i.get("total_count")})
    for i in monthly_resp_modified:
        main_dic.get(i.get("survey_id")).update({"m_m":i.get("total_count")})

    template_obj = MailTemplate.objects.get(template_name ="ROSHNIMIS Activity Mailer")
    subject = template_obj.subject +' - '+ today.strftime("%d/%m/%Y") 
    content = template_obj.content
    dynamic_content_act = ""
    dynamic_content_ben = ""
    table = '<table border=1 style="border-collapse: collapse;" class="table"> <thead> <tr> <th rowspan="2">{1}</th> <th colspan="2">Yesterday`s Responses</th> <th colspan="2">Current Week Response</th> <th colspan="2">Current Month Response</th> <th rowspan="2">Total Responses</th> </tr> <tr> <th>Created</th> <th>Modified</th> <th>Created</th> <th>Modified</th> <th>Created</th> <th>Modified</th> <tr> </thead> <tbody> {0} </tbody> </table> </div>'
    
    for key, value in main_dic.items():
        if key not in beneficiary_ids:
            survey_name = value.get("name")
            yes_response_created = value.get("y_c")
            yes_response_modified = value.get("y_m")
            current_week_response_created = value.get("w_c")
            current_week_response_modified = value.get("w_m")
            current_month_response_created = value.get("m_c")
            current_month_response_modified = value.get("m_m")
            total_response        = value.get("t")
            dynamic_content_act = dynamic_content_act + "<tr>  <td>{0}</td> <td>{1}</td>  <td>{2}</td> <td>{3}</td> <td>{4}</td> <td>{5}</td> <td>{6}</td> <td>{7}</td> <tr>".format(survey_name , yes_response_created,yes_response_modified,current_week_response_created,current_week_response_modified,current_month_response_created,current_month_response_modified,total_response)

    for key in beneficiary_ids:
        value = main_dic[key]
        survey_name = value.get("name")
        yes_response_created = value.get("y_c")
        yes_response_modified = value.get("y_m")
        current_week_response_created = value.get("w_c")
        current_week_response_modified = value.get("w_m")
        current_month_response_created = value.get("m_c")
        current_month_response_modified = value.get("m_m")
        total_response        = value.get("t")
        dynamic_content_ben = dynamic_content_ben + "<tr>  <td>{0}</td> <td>{1}</td>  <td>{2}</td> <td>{3}</td> <td>{4}</td> <td>{5}</td> <td>{6}</td> <td>{7}</td> <tr>".format(survey_name , yes_response_created,yes_response_modified,current_week_response_created,current_week_response_modified,current_month_response_created,current_month_response_modified,total_response)
            
    beneficairy_dynamic_content = "<b><u>Beneficiaries Responses Summary</u></b> <br><br>"+table.format(dynamic_content_ben,"Beneficiaries")
    activity_dynamic_content = "<b><u>Activities Responses Summary</u></b> <br><br>"+table.format(dynamic_content_act,"Activities")
    content = content.replace("@@tbody",beneficairy_dynamic_content +" <br><br> "+ activity_dynamic_content)

    to_ = ';'.join(ACTIVITY_MAIL_RECIEVER)
    send_to_cc = ';'.join(ACTIVITY_MAIL_CC)
    send_to_bcc = ';'.join(ACTIVITY_MAIL_BCC)
    send_data_obj = MailData.objects.create(subject = subject,content = content,mail_to = to_,
                                        mail_cc =send_to_cc,mail_bcc =send_to_bcc,priority = 1,mail_status = 1, 
                                        template_name = template_obj )

    return send_data_obj

def attachment_email():
    today = datetime.now().date()
    previous_day = today-timedelta(days=1)
    template_obj = MailTemplate.objects.get(template_name ="House Hold Activity Mailer")
    send_to_cc = ''
    send_to_bcc = ''
    subject = template_obj.subject
    content = template_obj.content
    content = content.replace("@@date",str(previous_day))

    to_ = ';'.join(ACTIVITY_MAIL_RECIEVER)
    send_to_cc = ';'.join(ACTIVITY_MAIL_CC)
    send_data_obj = MailData.objects.create(subject = subject,content = content,mail_to = to_,
                                        mail_cc =send_to_cc,mail_bcc =send_to_bcc,priority = 1,mail_status = 1, 
                                        template_name = template_obj )
  

    send_data_obj.file_paths.append({"filename":"HouseHoldActivity.csv","file_path":"media/export_data/data_dump_survey_425_2021Sep02235336.xlsx","file_type":"csv"})
    send_data_obj.save()
    # send_mail(subject,message,"mis@akrspi.org",to_,fail_silently=False,html_message=html_message)

    return send_data_obj