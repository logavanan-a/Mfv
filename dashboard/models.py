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

class DashboardWidgetTypes(BaseContent):
    name = models.CharField(max_length=15,unique=True)

    def __str__(self):
        return self.name

class DashboardIndicatorFilter(BaseContent):
    name = models.CharField(max_length=30,null=True, blank=True)
    slug = models.SlugField('Slug', max_length=60, null=True, blank=True)
    chart_type = models.CharField(max_length=100, choices=(('SW','State wise'), ('TS','Time series')), null=True, blank=True)

    def __str__(self):
        return str(self.name)+' - '+str(self.get_chart_type_display())


class DashboardChartWidgets(BaseContent):
    title = models.CharField(max_length=100)
    stats_title = models.CharField('Statistics title',max_length=100, null=True, blank=True)
    label = models.CharField(max_length=500)
    widgetypes = models.ForeignKey(DashboardWidgetTypes,on_delete=models.DO_NOTHING)
    # userroles = models.ManyToManyField(UserRoles)
    indicator = models.ManyToManyField(DashboardIndicatorFilter,blank=True)
    widgetquery = models.TextField()
    survey_id = models.PositiveIntegerField(default=0)
    chart_type = models.CharField(max_length=100, choices=(('NC','Normal Chart'), ('CC','Comparative Charts'), ('SW','State wise'), ('TS','Time series')), default="NC", null=True, blank=True)
    chart_size = models.CharField(max_length=25, null=True, blank=True)
    chart_header = models.CharField(max_length=250, null=True, blank=True)
    haxis_title = models.CharField(max_length=100, null=True, blank=True)
    vaxis_title = models.CharField(max_length=100, null=True, blank=True)
    query_type = models.CharField(max_length=100, choices=(('ORM','ORM'), ('SQL','SQL'),('SQL_P','SQL with Params')), default="ORM", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    slug = models.SlugField('Slug', max_length=60, null=True, blank=True)
    slug_choice = models.CharField(max_length=100, choices=(('R','Report'), ('D','Dashboard')), null=True, blank=True)
    config = models.JSONField(default=dict,blank=True,null=True)
    
    def __str__(self):
        return str(self.title) + '-' + str(self.label)
