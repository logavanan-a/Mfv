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
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class District(BaseContent):
    name = models.CharField(max_length=50)
    state =  models.ForeignKey(State, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class Partner(BaseContent):
    name = models.CharField(max_length=50)
    district =  models.ForeignKey(District, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class Mission(BaseContent):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.partner.name

class Donor(BaseContent):
    name = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='image_folder/')
    Date_of_association = models.DateField()

    def __str__(self):
        return self.name
    
class MissionIndicatorCategory(BaseContent):
    name = models.CharField(max_length=50)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name

class MissionIndicator(BaseContent):
    name = models.CharField(max_length=50)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name




