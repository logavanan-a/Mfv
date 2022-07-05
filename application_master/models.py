from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

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

# class Mission(BaseContent):
#     MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
#     name = models.CharField(max_length=350)
#     mission_template = models.IntegerField(choices = MISSION_CHOICES)

#     def __str__(self):
#         return self.name
    
class Donor(BaseContent):
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to='image_folder/')
    Date_of_association = models.DateField()

    def __str__(self):
        return self.name
    
# class MissionIndicatorCategory(BaseContent):
#     name = models.CharField(max_length=350)
#     mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

#     def __str__(self):
#         return self.name
    
#     def sub_category(self):
#         return MissionIndicator.objects.filter(category = self)

# class MissionIndicator(BaseContent):
#     name = models.CharField(max_length=350)
#     category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)

#     def __str__(self):
#         return self.name

# class MissionForm(BaseContent):
#     TYPE_CHOICES = (
#         (1, 'Text'), 
#         (2, 'Radio'), 
#         (3, 'Number'), 
#         (4, 'File Upload'), 
#         (5, 'Date')
#     )
#     mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
#     field_name = models.CharField(max_length=350)
#     field_type = models.IntegerField(choices= TYPE_CHOICES)
#     required = models.BooleanField(default=True)
#     field_config = JSONField()

#     def __str__(self):
#         return self.mission.name
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class Mission(BaseContent):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length = 350)
    mission_template = models.IntegerField(choices = MISSION_CHOICES)

    def __str__(self):
        return self.name

class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.partner.name

class MissionIndicatorCategory(BaseContent):
    name = models.CharField(max_length = 350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    def __str__(self):
        return self.name
    
    def sub_category(self):
        return MissionIndicator.objects.filter(category = self)

class MissionIndicator(BaseContent):
    IT_CHOICES = ((1,'Gender Base'),(2,'Total'))
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)
    indicator_type = models.IntegerField(choices = IT_CHOICES, default = 1, max_length = 2)

    def __str__(self):
        return self.name

# class QuestionValidation(BaseContent):
#     question = models.ForeignKey(Question)
#     validation_type = models.CharField(
#         max_length=255, blank=True, null=True, choices=VALIDATION_TYPE)
#     max_value = models.CharField(max_length=255, blank=True, null=True)
#     min_value = models.CharField(max_length=255, blank=True, null=True)
#     validation_condition = models.CharField(choices=VALIDATION_CONDITIONS,
#                                     max_length=255, blank=True, null=True)
#     other_text2 = models.CharField(max_length=255, blank=True, null=True)
#     message = models.CharField(max_length=255, blank=True, null=True)

#     def __str__(self):
#         return self.name

#     def clean(self):
#         if (float(self.min_value) or 0) > (float(self.max_value) or float('inf')):
#             raise ValidationError({
#                 'min_value': 'Min value should be less than max value',
#             })

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
    field_config = JSONField()

    def __str__(self):
        return self.mission.name

class MissionQuastionChioce(BaseContent):
    mission_question = models.ForeignKey(MissionQuestion, on_delete = models.DO_NOTHING, blank=True, null=True)
    text = models.CharField(max_length=500)
    report_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.mission.name

# class JsonAnswer(BaseContent):
#     INTERFACE_TYPES = (('0','Web'),('1','App'),('2','Migrated Data'))
#     user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
#     mission = models.ForeignKey(Mission, on_delete=models.CASCADE, blank=True, null=True)
#     interface = models.CharField(choices=INTERFACE_TYPES,default=1,max_length=2)
#     response = JSONField(default={})

#     def __str__(self):
#         return self.mission.name





