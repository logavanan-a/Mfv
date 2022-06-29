from django.contrib.postgres.fields import JSONField
from django.db import models


class BaseContent(models.Model):
    ACTIVE_CHOICES = ((0, 'Deleted'), (2, 'Active'),(3,"Inactive"))
    active          = models.PositiveIntegerField(choices=ACTIVE_CHOICES,default=2)
    created         = models.DateTimeField(auto_now_add=True)
    modified        = models.DateTimeField(auto_now=True)
    listing_order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract    = True

class State(BaseContent):
    name = models.CharField(max_length=350)

    def __str__(self):
        return self.name

class District(BaseContent):
    name = models.CharField(max_length=350)
    state =  models.ForeignKey(State, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class Partner(BaseContent):
    name = models.CharField(max_length=350)
    district =  models.ForeignKey(District, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class Mission(BaseContent):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length=350)
    mission_template = models.IntegerField(choices = MISSION_CHOICES)

    def __str__(self):
        return self.name
    
class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.partner.name

class Donor(BaseContent):
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to='image_folder/')
    Date_of_association = models.DateField()

    def __str__(self):
        return self.name
    
class MissionIndicatorCategory(BaseContent):
    name = models.CharField(max_length=350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name
    
    def sub_category(self):
        return MissionIndicator.objects.filter(category = self)

class MissionIndicator(BaseContent):
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class MissionForm(BaseContent):
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
    field_config = JSONField()

    def __str__(self):
        return self.mission.name





