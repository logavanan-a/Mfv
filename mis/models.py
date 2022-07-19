from application_master.models import *

from django.contrib.auth.models import User
from django.db import models
from jsonfield import JSONField


# declare a new model with a name "Task"
class Task(BaseContent):
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Submitted for approval'), (3, 'Approved'), (4,  'Rejected'), (5, 'Cancelled'))
    name = models.CharField(max_length = 150)
    user = models.ForeignKey(User, on_delete = models.DO_NOTHING)
    project = models.ForeignKey(Project, on_delete = models.DO_NOTHING, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    task_status = models.IntegerField(choices = STATUS_CHOICES, default=1)
    extension_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Task"
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
    task = models.ForeignKey(Task, on_delete=models.DO_NOTHING, blank=True, null=True)
    response = JSONField(default=dict)

    class Meta:
        # ordering = ['-id']
        verbose_name_plural = "Mission Indicator Achievement"

    def __str__(self):
        return self.task.name
    

    











    






