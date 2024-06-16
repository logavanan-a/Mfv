from django.db import models

# Create your models here.


# from __future__ import unicode_literals
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib import admin
import six
from constants import OPTIONAL

from masterdata.manager import ActiveQuerySet
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
# Create your models here.


class BaseContentBase(models.base.ModelBase):

    def __iter__(self):
        return self.objects.all().__iter__()

    @staticmethod
    def register(mdl):
        if (not hasattr(mdl, 'Meta')) or getattr(
                getattr(mdl, '_meta', None),
                'abstract', True
        ):
            return mdl

        class MdlAdmin(admin.ModelAdmin):
            list_display = ['__str__'] + getattr(mdl, 'admin_method', []) + [i.name for i in mdl._meta.fields]
            search_fields =  [i for i in getattr(mdl, 'searching', [])]
            filter_horizontal = [i.name for i in mdl._meta.many_to_many]

        if hasattr(mdl, 'Admin'):
            class NewMdlAdmin(mdl.Admin, MdlAdmin):
                pass
            admin.site.register(mdl, NewMdlAdmin)

        else:
            admin.site.register(mdl, MdlAdmin)

    def __new__(cls, name, bases, attrs):
        mdl = super(BaseContentBase, cls).__new__(cls, name, bases, attrs)
        BaseContentBase.register(mdl)
        return mdl


class BaseContent(six.with_metaclass(BaseContentBase, models.Model)):
    # ---------comments-----------------------------------------------------#
    # BaseContent is the abstract base model for all
    # the models in the project
    # This contains created and modified to track the
    # history of a row in any table
    # This also contains switch method to deactivate one row if it is active
    # and vice versa
    # ------------------------ends here---------------------------------------------#

    ACTIVE_CHOICES = ((0, 'Deleted'), (2, 'Active'),(3,"Inactive"))
    active = models.PositiveIntegerField(choices=ACTIVE_CHOICES,
                                         default=2)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True,db_index = True)
    objects = ActiveQuerySet.as_manager()

    #                                        BaseContent
    class Meta:
        #-----------------------------------------#
        # Don't create a table in database
        # This table is abstract
        #--------------------ends here--------------------#
        abstract = True

    #                                        BaseContent
    def switch(self):   
        # Deactivate a model if it is active
        # Activate a model if it is inactive
        self.active = {2: 0, 0: 2}[self.active]
        self.save()

    #                                        BaseContent
    def copy(self, commit=True):
        # Create a copy of given item and save in database
        obj = self
        obj.pk = None
        if commit:
            obj.save()
        return obj

    #                                        BaseContent
    def __str__(self):
        for i in ['name', 'text']:
            if hasattr(self, i):
                return getattr(self, i, 'Un%sed' % i)
        if hasattr(self, '__str__'):
            return self.__str__()
        return super(BaseContent, self).__str__()

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
        'masterdata.MasterLookup', related_name='masterlookup_boundary_region', **OPTIONAL,on_delete=models.DO_NOTHING)
    ward_type = models.ForeignKey(
        'masterdata.MasterLookup', related_name='masterlookup_ward', **OPTIONAL,on_delete=models.DO_NOTHING)
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