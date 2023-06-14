from django.db import models
from application_master.models import *


# Create your models here.
class DashboardSummaryLog(BaseContent):
    #-------------------#
    # Store the history of the dashboard query execution.
    #--------------------#
    log_key = models.CharField(max_length=500, unique=True)
    last_successful_update = models.DateTimeField(blank=True, null=True)
    most_recent_update = models.DateTimeField(blank=True, null=True)
    most_recent_update_status = models.CharField(max_length=2500, blank=True, null=True)
    most_recent_update_time_taken_millis = models.IntegerField(default=0)

    def __str__(self):
        return self.log_key
