from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import PROTECT,DO_NOTHING
from django.contrib.postgres.fields import JSONField
# from django.utils.translation import ugettext_lazy as _
from application_master.models import BaseContent


# Create your models here.



# email templates table
class MailTemplate(BaseContent):
    created_by      = models.ForeignKey(User,on_delete=models.DO_NOTHING,blank=True,null=True)
    #short name for the template
    template_name   = models.CharField(max_length=50,unique=True) 
    #details of where this template is used
    description     = models.TextField(blank=True,null=True) 
    subject         = models.CharField(max_length=1000)
    content         = models.TextField()
    html_template = models.CharField(max_length=100,blank=True,null=True)
    def __str__(self):
        return self.template_name
    class Meta:
        verbose_name_plural = ("Mail Template")
    
    def __str__(self):
        return self.template_name

priority_status = ((1,'high'), (2, 'normal'))  
send_status = ((1,'new'), (2, 'makedToSend'),(3,'Sent'),(4,'Failed'),(5,'Ingnored'))
  
# email transacations table
class MailData(BaseContent):
    # this stores the final subject and content after replacing the placeholders with actual values
    subject       = models.CharField(max_length=1000)
    content       = models.TextField()
    mail_to       = models.TextField()
    mail_cc       = models.TextField(blank=True,null=True)
    mail_bcc      = models.TextField(blank=True,null=True)
    priority      = models.IntegerField(choices=priority_status,default = 2) 
    #(initally zero, updated to 1 when sent on first attempt, and +1 every subsequent attempt)
    send_attempt  = models.PositiveIntegerField(default=0) 
    #every attempt you update this value to now()
    time_last_attempt =  models.DateField(blank=True,null=True) 
    #choices  1-new, 2-makedToSend, 3-Sent, 4-Failed, 5-ignored
    mail_status          = models.IntegerField(choices=send_status,default = 1)
    #store stack trace of any exception while sending out this email 
    error_details = models.TextField(blank=True,null=True) 
    template_name      = models.ForeignKey(MailTemplate,on_delete=models.DO_NOTHING,blank=True,null=True)
    mode       = models.TextField(blank=True,null=True)
    file_paths = models.JSONField(default=list,help_text="file info should be in this format [ {'file_path':'example path','file_type':'text','filename':'example.text'}] ")

    def __str__(self):
        return self.template_name.template_name

## BATCH PROGRAM sending the email should query on - priority, created, send_attempts desc
