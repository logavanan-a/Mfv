from application_master.models import BaseContent, Mission, VisionCentre
from django.contrib.auth import get_user_model
from django.db import models
from jsonfield import JSONField

User = get_user_model()


class Task(BaseContent):
    STATUS_CHOICES = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'),)
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
    INTERFACE_TYPES = (('0','Web'),('1','App'),('2','Migrated Data'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    interface = models.CharField(choices = INTERFACE_TYPES, default = 0, max_length = 2)
    response = JSONField(default=dict)

    def __str__(self):
        return self.mission.name
    
    class Meta:
        verbose_name_plural = "Mission Indicator Achievement"

class MissionIndicatorTarget(BaseContent):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, blank=True, null=True)
    response = JSONField(default=dict)

    def __str__(self):
        return self.mission.name
    
    class Meta:
        verbose_name_plural = "Mission Indicator Target"










    






