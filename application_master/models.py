from django.contrib.auth.models import Group, User
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from jsonfield import JSONField
from constants import OPTIONAL
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


# BaseContent model represents a base class for content-related models.
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
    group = models.ManyToManyField(Group, blank=True)
    slug = models.SlugField(
        "SEO friendly url, use only aplhabets and hyphen", max_length=60,unique=True)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, blank=True, null=True)
    app_link = models.CharField(max_length=512, blank=True)
    icon = models.CharField(max_length=512, blank=True, null=True)
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
    
    def get_sub_menus(self):
        # model method to filter menus based parent id
        return Menus.objects.filter(parent=self).order_by('menu_order')

class State(BaseContent):
    #-------------------#
    # State model represents a state with its name and inherits from the BaseContent class.
    #--------------------#
    name = models.CharField(max_length=350, unique=True)

    class Meta: 
        ordering = ('name',)
        verbose_name_plural = "             State"

    def __str__(self):
        return self.name
    
class District(BaseContent):
    #-------------------#
    # district model represents a district with its name and parent as state.
    #--------------------#
    name = models.CharField(max_length=350, unique=True)
    state =  models.ForeignKey(State, on_delete = models.DO_NOTHING)

    class Meta: 
        ordering = ('name',)
        verbose_name_plural = "            District"

    def __str__(self):
        return self.name

class Partner(BaseContent):
    #-------------------#
    # Partner model represents a partner with its name and slug.
    #--------------------#
    name = models.CharField(max_length=350, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    partner_logo = models.ImageField(upload_to = 'image_folder/', blank=True, null=True)

    class Meta: 
        ordering = ('name',)
        verbose_name_plural = "          Partner"

    def __str__(self):
        return self.name
    
    def save(self):
        self.slug = slugify(self.name)
        super(Partner, self).save()

class UserPartnerMapping(BaseContent):
    #-------------------#
    # UserPartnerMapping model represents a user and partner relationship.
    # user is a one to one relationship for Auth User
    #--------------------#
    partner =  models.ForeignKey(Partner, on_delete = models.DO_NOTHING)
    user = models.OneToOneField(User, on_delete = models.CASCADE, blank=True, null=True)


    class Meta: 
        verbose_name_plural = "  User Partner Mapping"
        unique_together = ('partner', 'user')

    def __str__(self):
        return self.partner.name

class Donor(BaseContent):
    #-------------------#
    # Donor model represents a donor with its name and logo image field
    #--------------------#
    name = models.CharField(max_length=350)
    logo = models.ImageField(upload_to = 'image_folder/', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "     Donor"

    def __str__(self):
        return self.name
    
class Mission(BaseContent):
    #-------------------#
    # Mission model represents a mission with its name, slug, and additional attributes.
    #--------------------#

    MISSION_CHOICES = ((1,'Indicator'),(2,'Form'))
    name = models.CharField(max_length = 350, unique = True)
    short_description  = models.TextField(blank=True, null=True)
    mission_template = models.IntegerField(choices = MISSION_CHOICES, default = 1)
    slug = models.SlugField(max_length=100, unique = True) 
    age_group_option = models.IntegerField(default=1)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = "           Mission"

    def __str__(self):
        return self.name
    
    def save(self):
        self.slug = slugify(self.name)
        super(Mission, self).save()

    def get_absolute_url(self):
        return reverse("mis:mission_add", kwargs = {"slug": self.slug})

class PartnerMissionMapping(BaseContent):
    #-------------------#
    # PartnerMissionMapping model represents a partner and mission relationship.
    #--------------------#
    partner = models.ForeignKey(Partner, on_delete = models.DO_NOTHING, blank=True, null=True)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING, blank=True, null=True)

    class Meta:
        ordering = ('partner__name',)
        verbose_name_plural = "         Partner Mission Mapping"

    def __str__(self):
        return f"{self.partner.name} - {self.mission.name}"

class Project(BaseContent):
    #-------------------#
    # Project model represents a project with its name, slug, and additional attributes.
    #--------------------#
    name = models.CharField(max_length = 350)
    partner_mission_mapping =  models.ForeignKey(PartnerMissionMapping, on_delete = models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(District, on_delete = models.DO_NOTHING, blank=True, null=True)
    location = models.CharField(max_length = 350)
    additional_info = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('name',)
        unique_together = ('name', 'partner_mission_mapping')
        verbose_name_plural = "      Project"

    def __str__(self):
        return f"{self.name} - {self.partner_mission_mapping.mission.name} - {self.partner_mission_mapping.partner.name}"

    def get_project_donor_mapping(self):
        try:
            get_project_donor_mapping_obj = ProjectDonorMapping.objects.get(project = self).donor.name
        except:
            get_project_donor_mapping_obj = None
        return get_project_donor_mapping_obj

class ProjectDonorMapping(BaseContent):
    #-------------------#
    # ProjectDonorMapping model represents a project and donor relationship.
    #--------------------#
    project = models.OneToOneField(Project, on_delete=models.DO_NOTHING, primary_key=True) 
    donor =  models.ForeignKey(Donor, on_delete = models.DO_NOTHING, blank=True, null=True)

    class Meta:
        verbose_name_plural = "    Project Donor Mapping"

    def __str__(self):
        return f"{self.project.name} - {self.donor.name}"

    

class MissionIndicatorCategory(BaseContent):
    #-------------------#
    # MissionIndicatorCategory model represents a mission indicator category.
    # Mission is a foreign key for Mission
    #--------------------#
    CATEGORY_CHOICES = ((1,'Programme Indicator'),(2,'Finance Indicator'))
    name = models.CharField(max_length = 350)
    mission = models.ForeignKey(Mission, on_delete = models.DO_NOTHING, blank=True, null=True)
    category_type = models.IntegerField(choices = CATEGORY_CHOICES, default=1)
    label_configuration = models.IntegerField(default=1)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'mission')
        verbose_name_plural = "        Mission Indicator Category"

    def __str__(self):
        return f"{self.name} - {self.mission.name}"
    
    def sub_category(self):
        return MissionIndicator.objects.filter(category = self).order_by('listing_order')

class MissionIndicator(BaseContent):
    #-------------------#
    # MissionIndicator model represents a mission indicator.
    # Category is a foreign key for MissionIndicatorCategory
    #--------------------#
    IT_CHOICES = ((1,'Gender Base'),(2,'Total'),(3,'Actuals'),(4,'Actuals With Grants Received'))
    name = models.CharField(max_length=350)
    category = models.ForeignKey(MissionIndicatorCategory, on_delete = models.DO_NOTHING)
    indicator_type = models.IntegerField(choices = IT_CHOICES, default = 1)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "       Mission Indicator"
    
    def __str__(self):
        return f"{self.name} - {self.category.name}"

class MissionIndicatorTarget(BaseContent):
    mission_indicator = models.ForeignKey(MissionIndicator, on_delete=models.DO_NOTHING,blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.DO_NOTHING,null=True, blank=True)
    approved_budget   = models.PositiveIntegerField(blank = True, null = True)
    created_by = models.ForeignKey(User, on_delete = models.DO_NOTHING, blank=True, null=True)

    class Meta:
        verbose_name_plural = "   Mission Indicator Target"

    def __str__(self):
        return f"{self.mission_indicator.name} - {self.created_by.username}"

class UserProjectMapping(BaseContent):
    #-------------------#
    # UserProjectMapping model represents a user and project relationship.
    #--------------------#
    project =  models.ForeignKey(Project, on_delete = models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, on_delete = models.CASCADE, blank=True, null=True)
    deactivated_date = models.DateField(blank=True, null=True)

    class Meta: 
        verbose_name_plural = " User Project Mapping"

    def __str__(self):
        return self.project.name


class ProjectFiles(BaseContent):
    #-------------------#
    # ProjectFiles model represents a project file to upload.
    # Direct linkage with project model
    #--------------------#
    name = models.CharField(max_length=350) 
    project = models.ForeignKey(Project, on_delete = models.DO_NOTHING, blank=True, null=True)
    upload_file = models.FileField()
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='created_by')
    modified_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='modified_by')

    class Meta:
        verbose_name_plural = "Project Files"

    def __str__(self):
        return self.project.name


class BoundaryLevel(BaseContent):
    name = models.CharField('Name', max_length=100)
    code = models.PositiveIntegerField(**OPTIONAL)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING,**OPTIONAL)

    def __str__(self):
        """Return Name."""
        return str(self.name)

    def get_next_level(self):
        next_level = None
        try:
            next_level = BoundaryLevel.objects.filter(code__gt=self.code,active=2).order_by('code')[0]
        except:
            pass
        return next_level

    def get_level_count(self):
        objlist = Boundary.objects.filter(active=2,boundary_level_type = self)
        count = objlist.count() if objlist else 0
        return count

    def next_levels(self):
        levels = map(str, list(set(BoundaryLevel.objects.filter(code__gt=self.code).order_by('code').values_list('code', flat=True))))
        return ','.join(levels)

    def next_levels_code(self):
        levels = (BoundaryLevel.objects.filter(code__gte=self.code,active=2).order_by('code'))
        return levels

class Boundary(BaseContent):
    """Table to Save DIfferent Locations based on Level."""
    region = models.ForeignKey(
        'application_master.MasterLookup', related_name='masterlookup_boundary_region', **OPTIONAL,on_delete=models.DO_NOTHING)
    ward_type = models.ForeignKey(
        'application_master.MasterLookup', related_name='masterlookup_ward', **OPTIONAL,on_delete=models.DO_NOTHING)
    name = models.CharField('Name', max_length=100)
    code = models.CharField('Code', max_length=100, **OPTIONAL)
    boundary_level = models.IntegerField(default=0)
    boundary_level_type = models.ForeignKey(BoundaryLevel, **OPTIONAL,on_delete=models.DO_NOTHING)
    desc = models.TextField('Description', **OPTIONAL)
    slug = models.SlugField('Slug', max_length=255, **OPTIONAL)
    parent = models.ForeignKey('self',**OPTIONAL,on_delete=models.DO_NOTHING)
    latitude = models.CharField(max_length=100, **OPTIONAL)
    longitude = models.CharField(max_length=100, **OPTIONAL)
    _polypoints = models.CharField(default='[]', max_length=500, **OPTIONAL)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, **OPTIONAL)
    object_id = models.PositiveIntegerField(**OPTIONAL)
    content_object = GenericForeignKey('content_type', 'object_id')
    udf1 = models.PositiveIntegerField(default=0)
    short_code = models.CharField('Short Code', max_length=100)


    def __str__(self):
        """Return Name."""
        return self.name
    

    def get_county(self):
        """Return the Country for the level 2."""
        return Boundary.objects.filter(parent=self)

    def get_parent_locations(self, prev_loc=[]):
        """ Returns the parent level objects """
        parent = self.parent
        if parent:
            if parent.parent:
                prev_loc.append(
                    {'level' + str(parent.boundary_level_type.code) + '_id': str(parent.id)})
                parent.get_parent_locations(prev_loc)
            else:
                prev_loc.append(
                    {'level' + str(parent.boundary_level_type.code) + '_id': str(parent.id)})
            return prev_loc
        elif not parent and not prev_loc:
            return []
    
    def get_facility_data(self):
        object_id = 0
        urban = 'location-urban'
        rural = 'location-rural'
        if self.boundary_level >= 4:
            if self.object_id:
                mast = MasterLookUp.objects.get(id=self.object_id)
                object_id = mast.id
        else:
            mast = MasterLookUp.objects.get(slug__iexact=rural)
            object_id = mast.id
        return object_id

    class Meta:
        ordering = ['name']

class MasterLookUp(BaseContent):
    name = models.CharField(max_length=400)
    parent = models.ForeignKey('self',on_delete=models.DO_NOTHING, **OPTIONAL)
    slug = models.SlugField(_("Slug"), blank=True)
    code = models.IntegerField(default=0)
    order = models.FloatField(default=0,null=True,blank=True)
    choice_id = models.IntegerField(default=0)
    skip_question = models.JSONField(default=list,**OPTIONAL)


    def __str__(self):
        return str(self.name)

    def get_child(self):
        child_obj = MasterLookUp.objects.filter(active=2, parent__id=self.id)
        child_list = []
        if child_obj:
            for i in child_obj:
                child_list.append(
                    {'id': i.id, 'name': i.name, 'child': i.get_child(), 'parent_id': self.id})
            return child_list
        else:
            return child_list

    def get_child_data(self):
        child_objlist = MasterLookUp.objects.filter(active=2, parent__id=self.id).order_by("-id")
        return child_objlist

    # def get_masterdata_locations(self):
    #     locations = MasterDataLocation.objects.filter(masterdata=self,active=2).values_list('location',flat=True)
    #     if not locations :
    #         locations=""
    #     else:
    #         locations= ','.join(str(i) for i in locations)
    #     return locations