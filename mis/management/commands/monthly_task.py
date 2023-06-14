import datetime

from application_master.models import Project
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from mis.models import Task

today_date = datetime.date.today()

class Command(BaseCommand):
    """
    A custom Django management command that performs an operation for users in the "Partner Data Entry Operator" group
    and all projects in the system.
    """
    def handle(self, *args, **kwargs):
        """
        Iterates over users in the "Partner Data Entry Operator" group and all projects,
        creating a string concatenation for each project.
        """
        for user_obj in User.objects.filter(groups__name = 'Partner Data Entry Operator'):
            for project in Project.objects.all():
                string_cancate = project.partner_mission_mapping.mission.name +" - "+project.name+" - April 2022"
