from application_master.models import *

from django.contrib.auth.models import User
from django.db import models
from jsonfield import JSONField
from datetime import date
from datetime import  timedelta


# declare a new model with a name "Task"
class Task(BaseContent):
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Submitted for Partner Admin'),(3, 'Submitted for Project In-charge'), (4, 'Approved'), (5,  'Rejected'))
    name = models.CharField(max_length = 150)
    user = models.ForeignKey(User, on_delete = models.DO_NOTHING)
    project = models.ForeignKey(Project, on_delete = models.DO_NOTHING, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    task_status = models.IntegerField(choices = STATUS_CHOICES, default=1)
    extension_date = models.DateField(blank=True, null=True)
    task_approval = models.ForeignKey(User, on_delete = models.CASCADE, blank=True, null=True, related_name='task_approval')
    project_in_charge = models.ForeignKey(User, on_delete = models.CASCADE, blank=True, null=True, related_name='project_in_charge')


    

    class Meta:
        verbose_name_plural = " Task"
        ordering = ['-id']

    def __str__(self):
        return self.name

    # function to initialize the model, task list edit mission indicator
    def get_task(self):
        try:
            obj =  MissionIndicatorAchievement.objects.get(task = self)
        except:
            obj = None
        return obj

# declare a new model with a name "MissionIndicatorAchievement"
class MissionIndicatorAchievement(BaseContent):
    CAMP_OPTION=(
        (1, 'Drivers'),
        (2, 'Truckers'),
        (3, 'Carpenters')
    )
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, blank=True, null=True)
    response = JSONField(default=dict)
    number_working_days = models.IntegerField(default=0)
    project_reference_file = models.FileField(upload_to='file/%Y/%m/%d',blank=True, null=True)
    camp_organized = models.IntegerField(choices = CAMP_OPTION, blank=True, null=True)
    class Meta:
        # ordering = ['-id']
        verbose_name_plural = "Mission Indicator Achievement"

    def __str__(self):
        return self.task.name
    

    











    






