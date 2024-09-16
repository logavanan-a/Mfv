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
        parser.add_argument('-td', '--task_date', type=str,help='Task start date')
        parser.add_argument('-p', '--project', type=str,help='Project Id')

    def handle(self, *args, **kwargs):
        """
        Iterates over users in the "Partner Data Entry Operator" group and all projects,
        creating a string concatenation for each project.
        """
        task_date = kwargs.get('task_date')
        p_id = kwargs.get('project')
        if not task_date:
            return 'Please provide valid date for task in the format dd/mm/yyyy (e.g. -td 01/01/2019)'
        from_date = datetime.datetime.strptime(task_date, "%d/%m/%Y").date()
        if p_id:
            projects = Project.objects.filter(id__in=p_id.split(','),active=2,partner_mission_mapping__mission_id=5).order_by('name')
        else:
            projects = Project.objects.filter(active=2,partner_mission_mapping__mission_id=5).order_by('name')
        end_date = from_date.replace(day=calendar.monthrange(from_date.year, from_date.month)[1])
        multiple_projects_users, multiple_partner_users, created_tasks = [], [], []
        for project in projects:
            # for partner_mapping in UserProjectMapping.objects.filter(project=project, active=2).order_by('-modified'):
            try:
                # getting the user and project mapped records
                project_incharge = UserProjectMapping.objects.filter(user__groups__id=2,project=project, active=2)
                data_entry_op = UserProjectMapping.objects.filter(user__groups__id=4,project=project, active=2)
                partner_mapping = UserProjectMapping.objects.filter(user__groups__id=1,project=project, active=2)

                # user_partner_mapping = UserPartnerMapping.objects.filter(
                #     partner=project.partner_mission_mapping.partner, active=2).order_by('-modified')

                # if project_incharge.count() != 1:
                #     multiple_projects_users.append(project.name)
                #     continue
                # if user_partner_mapping.count() != 1:
                #     multiple_partner_users.append(
                #         project.partner_mission_mapping.partner)
                #     continue
                task_data = {
                    'user': partner_mapping.first().user if partner_mapping else None,
                    'end_date': end_date,
                    'task_status': 1,
                    'task_month': from_date.month,
                    'task_approval': data_entry_op.first().user if data_entry_op else None,
                    'project_in_charge': project_incharge.first().user if project_incharge else None,
                }
                new_task, created = Task.objects.update_or_create(
                    name=project.name,
                    project=project,
                    start_date=from_date,
                    defaults=task_data,
                )
                created_tasks.append(new_task.name)
            except:
                continue

        # print("Please check these projects have multiple user mapping or doesn't have mapping ")
        # print("----------------------------------------------------------------------------------")
        # print(set(multiple_projects_users))
        # print("----------------------------------------------------------------------------------\n")

        # print(
        #     "Please check these partner have multiple user mapping or doesn't have mapping ")
        # print("----------------------------------------------------------------------------------")
        # print(multiple_partner_users)
        # print("----------------------------------------------------------------------------------\n")

        print("These tasks are created successfully")
        print("----------------------------------------------------------------------------------")
        print(set(created_tasks))
        print("----------------------------------------------------------------------------------")
