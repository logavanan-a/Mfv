from application_master.models import BaseContent, Mission, VisionCentre
from django.contrib.auth import get_user_model
from django.db import models
from jsonfield import JSONField

User = get_user_model()


class Task(BaseContent):
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Submitted for approval'), (3, 'Approved'), (4,  'Rejected'), (5, 'Cancelled'))
        
    name = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    vision_centre = models.ForeignKey(VisionCentre, on_delete=models.CASCADE, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    task_status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    extension_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Task"

class MissionIndicatorAchievement(BaseContent):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    response = JSONField(default=dict)

    def __str__(self):
        return self.task.name
    
    class Meta:
        verbose_name_plural = "Mission Indicator Achievement"










    






