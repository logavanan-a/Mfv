from django.contrib.auth import get_user_model
from django.db import models
# from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
from jsonfield import JSONField
from django.urls import reverse


User = get_user_model()

class BaseContent(models.Model):
    ACTIVE_CHOICES  = ((0, 'Deleted'), (2, 'Active'),(3,"Inactive"))
    active          = models.PositiveIntegerField(choices = ACTIVE_CHOICES, default = 2)
    created         = models.DateTimeField(auto_now_add = True)
    modified        = models.DateTimeField(auto_now = True)
    listing_order   = models.PositiveIntegerField(default = 0)

    class Meta:
        abstract    = True

class State(BaseContent):
    name = models.CharField(max_length=350)

    def __str__(self):
        return self.name
    
    class Meta: 
        verbose_name_plural = "State"

class District(BaseContent):
    name = models.CharField(max_length=350)
    state =  models.ForeignKey(State, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

    class Meta: 
        verbose_name_plural = "District"

class Partner(BaseContent):
    name = models.CharField(max_length=350)
    slug = models.SlugField(max_length=100, default="")
    # district =  models.ForeignKey(District, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name
    
    class Meta: 
        verbose_name_plural = "Partner"

    # def save(self, *args, **kwargs):
    #     self.slug = self.slug or slugify(self.title)
    #     super().save(*args, **kwargs)

class UserPartnerMapping(BaseContent):
    partner =  models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.partner.name

    class Meta: 
        verbose_name_plural = "User Partner Mapping"
        unique_together = ('partner', 'user')

class Donor(BaseContent):
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to='image_folder/')
    Date_of_association = models.DateField()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Donor"
    
class Mission(BaseContent):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length = 350)
    mission_template = models.IntegerField(choices = MISSION_CHOICES)
    slug = models.SlugField(max_length=100, default="")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Mission"

    def get_absolute_url(self):
        return reverse("mis:mission_detail", kwargs={"slug": self.slug})

class VisionCentre(BaseContent):
    name = models.CharField(max_length = 350)
    partner =  models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
    district =  models.ForeignKey(District, on_delete = models.DO_NOTHING)
    location = models.CharField(max_length = 350)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Vision Centre"

class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.partner.name
    
    class Meta:
        verbose_name_plural = "Partner Mission Mapping"

class MissionIndicatorCategory(BaseContent):
    CATEGORY_CHOICES = ((1,'Program Indicator'),(2,'Finace Indicator'),(3, 'Income & Expense'))
    name = models.CharField(max_length = 350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
    category_type = models.IntegerField(choices = CATEGORY_CHOICES, default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Mission Indicator Category"

    def sub_category(self):
        return MissionIndicator.objects.filter(category = self)

class MissionIndicator(BaseContent):
    IT_CHOICES = ((1,'Gender Base'),(2,'Total'))
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)
    indicator_type = models.IntegerField(choices = IT_CHOICES, default = 1)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Mission Indicator"


class MissionQuestion(BaseContent):
    TYPE_CHOICES = (
        (1, 'Text'), 
        (2, 'Radio'), 
        (3, 'Number'), 
        (4, 'File Upload'), 
        (5, 'Date')
    )
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
    field_name = models.CharField(max_length=350)
    field_type = models.IntegerField(choices= TYPE_CHOICES)
    required = models.BooleanField(default=True)
    field_config = JSONField(default=dict)

    def __str__(self):
        return self.mission.name
    
    class Meta:
        verbose_name_plural = "Mission Question"

class MissionQuastionChioce(BaseContent):
    mission_question = models.ForeignKey(MissionQuestion, on_delete = models.DO_NOTHING, blank=True, null=True)
    text = models.CharField(max_length=500)
    report_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.mission.name

    class Meta:
        verbose_name_plural = "Mission Quastion Chioce"





