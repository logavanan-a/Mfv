from django.db import models
from application_master.models import *
from django.contrib.postgres.fields import ArrayField


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


ACTIVE_CHOICES = (
    (1, 'Submitted for Approval'), # once submitted for approval from app it will goes to parter admin
    (2, 'submitted for Project In-charge'), # once partner admin reveiwed and submitted to Project In-charge
    (3, 'Approved'), # once project incharge approved , final status
    (4, 'Rejected'), # when partner admin rejected the record
)
class MonthlyDashboard(BaseContent):
    creation_key = models.CharField(max_length=75, unique=True)
    month = models.IntegerField('Month(YYYYMM)')
    children_covered_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    children_covered_count = models.IntegerField(default=0)
    school_covered_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    school_covered_count = models.IntegerField(default=0)
    teachers_train_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    teachers_train_count = models.IntegerField(default=0)
    children_pres_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    children_pres_count = models.IntegerField(default=0)
    child_prov_spec_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    child_prov_spec_count = models.IntegerField(default=0)
    pgp_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    pgp_count = models.IntegerField(default=0)
    children_reffered_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    children_reffered_count = models.IntegerField(default=0)
    child_prov_hos_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    child_prov_hos_count = models.IntegerField(default=0)
    children_adv_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    children_adv_count = models.IntegerField(default=0)
    children_prov_sgy_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    children_prov_sgy_count = models.IntegerField(default=0)
    swc_uuid = ArrayField(ArrayField(models.CharField(max_length=75, blank=True),),)
    swc_count = models.IntegerField(default=0)
    current_status = models.IntegerField(default=0,choices = ACTIVE_CHOICES)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='data_entry_operator',)
    partner_admin = models.ForeignKey(User, on_delete=models.CASCADE,**OPTIONAL,related_name='partner_admin',)
    partner_submitted = models.DateField(**OPTIONAL)
    project_incharge = models.ForeignKey(User, on_delete=models.CASCADE,**OPTIONAL,related_name='project_incharge',)
    project_incharge_submitted = models.DateField(**OPTIONAL)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)

    def __str__(self):
        return f"Coverage Data for {self.month}"

class Remarks(BaseContent):
    user = models.ForeignKey(User, on_delete=models.CASCADE, **OPTIONAL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    remark = models.CharField(max_length=500)