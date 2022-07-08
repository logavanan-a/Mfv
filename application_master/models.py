from django.contrib.auth.models import Group, User
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from jsonfield import JSONField


class BaseContent(models.Model):
    ACTIVE_CHOICES  = ((0, 'Deleted'), (2, 'Active'),(3,"Inactive"))
    active          = models.PositiveIntegerField(choices = ACTIVE_CHOICES, default = 2)
    created         = models.DateTimeField(auto_now_add = True)
    modified        = models.DateTimeField(auto_now = True)
    listing_order   = models.PositiveIntegerField(default = 0)

    class Meta:
        abstract    = True


class Menus(BaseContent):
    #-------------------#
    # Menus module
    # parent is a foriegn key
    # slug field is used
    #--------------------#
    name = models.CharField(max_length=100)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60,unique=True)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, blank=True, null=True)
    backend_link = models.CharField(max_length=512, blank=True)
    icon = models.CharField(max_length=512, blank=True)
    menu_order = models.IntegerField(null=True, blank=True)
    inner_display = models.BooleanField(default=False)

    class Meta:
        ordering = ('menu_order',)
        verbose_name_plural = 'Menus'

    def __str__(self):
        # string method to return name
        hairarchy_name = self.name
        if self.parent:
            hairarchy_name = hairarchy_name +'--'+ self.parent.name
            if self.parent.parent:
                hairarchy_name = hairarchy_name +'--'+ self.parent.parent.name
        return hairarchy_name


class State(BaseContent):
    name = models.CharField(max_length=350)

    class Meta: 
        verbose_name_plural = "State"

    def __str__(self):
        return self.name
    
class District(BaseContent):
    name = models.CharField(max_length=350)
    state =  models.ForeignKey(State, on_delete = models.DO_NOTHING)

    class Meta: 
        verbose_name_plural = "District"

    def __str__(self):
        return self.name

class Partner(BaseContent):
    name = models.CharField(max_length=350)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta: 
        verbose_name_plural = "Partner"

    def __str__(self):
        return self.name
    
    def save(self):
        self.slug = slugify(self.name)
        super(Partner, self).save()

class UserPartnerMapping(BaseContent):
    partner =  models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    class Meta: 
        verbose_name_plural = "User Partner Mapping"
        unique_together = ('partner', 'user')

    def __str__(self):
        return self.partner.name


class Donor(BaseContent):
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to='image_folder/')
    Date_of_association = models.DateField()

    class Meta:
        verbose_name_plural = "Donor"

    def __str__(self):
        return self.name
    
    
class Mission(BaseContent):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length = 350)
    mission_template = models.IntegerField(choices = MISSION_CHOICES)
    slug = models.SlugField(max_length=100, unique = True) 

    class Meta:
        verbose_name_plural = "Mission"

    def __str__(self):
        return self.name
    
    def save(self):
        self.slug = slugify(self.name)
        super(Mission, self).save()

    def get_absolute_url(self):
        return reverse("mis:mission_add", kwargs={"slug": self.slug})

class VisionCentre(BaseContent):
    name = models.CharField(max_length = 350)
    partner =  models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
    district =  models.ForeignKey(District, on_delete = models.DO_NOTHING)
    location = models.CharField(max_length = 350)

    class Meta:
        verbose_name_plural = "Vision Centre"

    def __str__(self):
        return self.name


class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Partner Mission Mapping"

    def __str__(self):
        return self.partner.name
    

class MissionIndicatorCategory(BaseContent):
    CATEGORY_CHOICES = ((1,'Program Indicator'),(2,'Finance Indicator'))
    name = models.CharField(max_length = 350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING)
    category_type = models.IntegerField(choices = CATEGORY_CHOICES, default=1)

    class Meta:
        verbose_name_plural = "Mission Indicator Category"

    def __str__(self):
        return self.name
    
    


    def sub_category(self):
        return MissionIndicator.objects.filter(category = self)

class MissionIndicator(BaseContent):
    IT_CHOICES = ((1,'Gender Base'),(2,'Total'))
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)
    indicator_type = models.IntegerField(choices = IT_CHOICES, default = 1)

    class Meta:
        verbose_name_plural = "Mission Indicator"

    def __str__(self):
        return self.name
    

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

    class Meta:
        verbose_name_plural = "Mission Question"

    def __str__(self):
        return self.mission.name
    

class MissionQuastionChioce(BaseContent):
    mission_question = models.ForeignKey(MissionQuestion, on_delete = models.DO_NOTHING, blank=True, null=True)
    text = models.CharField(max_length=500)
    report_code = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Mission Quastion Chioce"

    def __str__(self):
        return self.mission.name

class MissionIndicatorTarget(BaseContent):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    mission_indicator = models.ForeignKey(MissionIndicator, on_delete=models.CASCADE, blank=True, null=True)
    target = models.IntegerField()
    periodicity_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Mission Indicator Target"

    def __str__(self):
        return f"{self.mission_indicator.name} - {created_by.username}"
    
