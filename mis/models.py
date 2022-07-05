from application_master.models import *
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# class MissionData(models.Model):
#     created_on = models.ForeignKey(User, on_delete=models.CASCADE)
#     mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
#     response = JSONField(default={})

class MissionResponse(BaseContent):
    INTERFACE_TYPES = (('0','Web'),('1','App'),('2','Migrated Data'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, blank=True, null=True)
    interface = models.CharField(choices = INTERFACE_TYPES, default = 0, max_length = 2)
    response = JSONField(default={})

    def __str__(self):
        return self.mission.name




    






