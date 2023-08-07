import datetime
from application_master.models import Project
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from mis.models import Task
import calendar
from application_master.models import UserProjectMapping, UserPartnerMapping


today_date = datetime.date.today()


class Command(BaseCommand):
    """
    A custom Django management command that performs an operation for users in the "Partner Data Entry Operator" group
    and all projects in the system.
    """
    help = 'Command for create the task list'

    def add_arguments(self, parser):
        # parser.add_argument('-f', '--from', type=int,
        #                     help='From month to copy')
        parser.add_argument('-td', '--task_date', type=str,
                            help='Task start date')

    def handle(self, *args, **kwargs):
        """
        Iterates over users in the "Partner Data Entry Operator" group and all projects,
        creating a string concatenation for each project.
        """
        task_date = kwargs.get('task_date')
        from_date = datetime.datetime.strptime(task_date, "%d/%m/%Y").date()

        projects = Project.objects.filter(active=2).order_by('name')
        end_date = from_date.replace(day=calendar.monthrange(
            from_date.year, from_date.month)[1])
        multiple_projects_users, created_tasks = [], []
        for project in projects:
            try:
                project_incharge = UserProjectMapping.objects.get(
                    project=project, active=2)
                user_partner_mapping = UserPartnerMapping.objects.filter(
                    partner=project.partner_mission_mapping.partner, active=2)
                task_data = {
                    'user': user_partner_mapping.first().user,
                    'end_date': end_date,
                    'task_status': 1,
                    'task_month': from_date.month,
                    'task_approval': user_partner_mapping.first().user,
                    'project_in_charge': project_incharge.user if project_incharge else None,
                }
                new_task, created = Task.objects.update_or_create(
                    name=project.name,
                    project=project,
                    start_date=from_date,
                    defaults=task_data,
                )
                created_tasks.append(new_task.name)
            except:
                multiple_projects_users.append(project.name)

        print("Please check these projects have multiple user mapping or doesn't have mapping ")
        print("----------------------------------------------------------------------------------")
        print(multiple_projects_users)
        print("----------------------------------------------------------------------------------\n")

        print("These tasks are created successfully")
        print("----------------------------------------------------------------------------------")
        print(created_tasks)
        print("----------------------------------------------------------------------------------")
