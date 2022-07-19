from django.contrib.auth.models import Group, User
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from jsonfield import JSONField


class BaseContent(models.Model):
    ACTIVE_CHOICES  = ((2, 'Active'),(0,"Inactive"))
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
    group = models.ForeignKey(Group, on_delete=models.DO_NOTHING, blank=False, null=False)
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60,unique=True)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, blank=True, null=True)
    app_link = models.CharField(max_length=512, blank=True)
    menu_order = models.IntegerField(null=True, blank=True)

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
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)

    class Meta: 
        verbose_name_plural = "User Partner Mapping"
        unique_together = ('partner', 'user')

    def __str__(self):
        return self.partner.name

class Donor(BaseContent):
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to = 'image_folder/', blank=True)

    class Meta:
        verbose_name_plural = "Donor"

    def __str__(self):
        return self.name
    
class Mission(BaseContent):
    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length = 350, unique = True)
    mission_template = models.IntegerField(choices = MISSION_CHOICES, default = 1)
    slug = models.SlugField(max_length=100, unique = True) 

    class Meta:
        verbose_name_plural = "Mission"

    def __str__(self):
        return self.name
    
    def save(self):
        self.slug = slugify(self.name)
        super(Mission, self).save()

    def get_absolute_url(self):
        return reverse("mis:mission_add", kwargs = {"slug": self.slug})

class PartnerMissionMapping(BaseContent):
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING, blank=True, null=True)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Partner Mission Mapping"

    def __str__(self):
        return f"{self.partner.name} - {self.mission.name}"

class Project(BaseContent):
    name = models.CharField(max_length = 350)
    partner_mission_mapping =  models.ForeignKey(PartnerMissionMapping, on_delete = models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(District, on_delete = models.DO_NOTHING, blank=True, null=True)
    location = models.CharField(max_length = 350)

    class Meta:
        unique_together = ('name', 'partner_mission_mapping')
        verbose_name_plural = "Project"

    def __str__(self):
        return self.name

class ProjectDonorMapping(BaseContent):
    project = models.OneToOneField(Project, on_delete=models.DO_NOTHING, primary_key=True) 
    donor =  models.ForeignKey(Donor, on_delete = models.DO_NOTHING, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Project Donor Mapping"

    def __str__(self):
        return f"{self.project.name} - {self.donor.name}"

class MissionIndicatorCategory(BaseContent):
    CATEGORY_CHOICES = ((1,'Program Indicator'),(2,'Finance Indicator'))
    name = models.CharField(max_length = 350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING, blank=True, null=True)
    category_type = models.IntegerField(choices = CATEGORY_CHOICES, default=1)

    class Meta:
        verbose_name_plural = "Mission Indicator Category"

    def __str__(self):
        return f"{self.name} - {self.mission.name}"
    
    def sub_category(self):
        return MissionIndicator.objects.filter(category = self)

class MissionIndicator(BaseContent):
    IT_CHOICES = ((1,'Gender Base'),(2,'Total'))
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)
    indicator_type = models.IntegerField(choices = IT_CHOICES, default = 1)

    class Meta:
        verbose_name_plural = "Mission Indicator"

class MissionIndicatorTarget(BaseContent):
    mission_indicator = models.ForeignKey(MissionIndicator, on_delete=models.DO_NOTHING, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING, blank=True, null=True)
    target = models.IntegerField()
    periodicity_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Mission Indicator Target"

    def __str__(self):
        return f"{self.mission_indicator.name} - {self.created_by.username}"

class ProjectFiles(BaseContent):
    name = models.CharField(max_length=350) 
    project = models.ForeignKey(Project, on_delete = models.DO_NOTHING, blank=True, null=True)
    upload_file = models.FileField()
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='created_by')
    modified_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='modified_by')

    class Meta:
        verbose_name_plural = "Project Files"

    def __str__(self):
        return self.project.name