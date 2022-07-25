import datetime

from application_master.models import Project
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from mis.models import Task

today_date = datetime.date.today()

class Command(BaseCommand):
    # Monthly Task Creat.     
    # def add_arguments(self, parser):
    #     parser.add_argument('year', type=int, help='Task date to be created')

    def handle(self, *args, **kwargs):
        
        for user_obj in User.objects.filter(groups__name = 'Partner Data Entry Operator'):
            for project in Project.objects.all():
                string_cancate = project.partner_mission_mapping.mission.name +" - "+project.name+" - April 2022"
                print(string_cancate)
                # added = Task(project = project,user=user_obj, name = string_cancate, start_date="2022-04-01",end_date= "2022-04-30")
                # added.save()
