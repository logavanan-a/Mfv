from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin,ImportExportModelAdmin, ImportExportMixin
from django.contrib.auth.models import User
from survey.admin import ImportExportFormat
from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget, Partner,
                                       PartnerMissionMapping, Project,
                                       ProjectDonorMapping, ProjectFiles,
                                       State, UserPartnerMapping,UserProfile,
                                       UserProjectMapping,MasterLookUp,Boundary,BoundaryLevel)

# @admin.register(BoundaryLevel)
# @admin.register(Boundary)

@admin.register(BoundaryLevel)
class AdminBoundaryLevel(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Partner' model.
    """
    search_fields = ['name', 'slug']
    list_filter = ['active']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Boundary)
class AdminBoundary(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Partner' model.
    """
    search_fields = ['name', 'slug']
    list_filter = ['active','boundary_level_type']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

class MissionIndicatorCategoryInline(admin.TabularInline): #StackedInline
    model = MissionIndicatorCategory
    extra = 0

class UserInline(admin.TabularInline): #StackedInline
    model = User
    extra = 0

@admin.register(Mission)
class AdminMission(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Custom admin configuration for the 'Mission' model.
    ImportExportActionModelAdmin provides the import/export functionality for the admin page.
    """
    exclude = ['mission_template']
    inlines = [MissionIndicatorCategoryInline]
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserProjectMapping)
class AdminUserProjectMapping(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'UserProjectMapping' model.
    """
    search_fields = ['project__name','user__username']
    list_filter = ['active','user__groups','project']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(State)
class AdminState(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'State' model.
    """
    search_fields = ['name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(District)
class AdminDistrict(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'District' model.
    """
    search_fields = ['name']
    list_filter = ['state']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(Project)
class AdminProject(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Project' model.
    """
    search_fields = ['name', 'partner_mission_mapping__partner__name']
    list_filter = ['active','partner_mission_mapping__partner']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(MissionIndicatorCategory)
class AdminMissionIndicatorCategory(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'MissionIndicatorCategory' model.
    """
    search_fields = ['name']
    list_filter = ['mission__name', 'category_type']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicator)
class AdminMissionIndicator(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'MissionIndicator' model.
    """
    search_fields = ['name']
    list_filter = ['category__name', 'indicator_type', 'category__mission__name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(Donor)
class AdminDonor(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Donor' model.
    """
    search_fields = ['name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(PartnerMissionMapping)
class AdminPartnerMissionMapping(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'PartnerMissionMapping' model.
    """
    search_fields = ['partner__name', 'mission__name']
    list_filter = ['mission__name', 'partner__name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(Partner)
class AdminPartner(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Partner' model.
    """
    search_fields = ['name', 'slug']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('name',)}

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(MissionIndicatorTarget)
class AdminMissionIndicatorTarget(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'MissionIndicatorTarget' model.
    """
    search_fields = ['mission_indicator__name', 'project__name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(UserPartnerMapping)
class AdminUserPartnerMapping(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'UserPartnerMapping' model.
    """
    search_fields = ['partner__name', 'user__username']
    list_filter = ['active','user__groups','partner']
    list_display = ('user', 'get_group_name','partner')  # Add 'get_group_name' to display in admin

    # def get_list_display(self, request):
    #     """
    #     Customize the list display for the admin page.
    #     """
    #     return [field.name for field in self.model._meta.concrete_fields]

    def get_group_name(self, obj):
        return obj.user.groups.first().name if obj.user.groups.exists() else '-'  # Fetch the group name

    get_group_name.short_description = 'Group'  # Display name in admin
@admin.register(ProjectDonorMapping)
class AdminProjectDonorMapping(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'ProjectDonorMapping' model.
    """
    search_fields = ['donor__name', 'project__name']
    list_filter = ['donor__name']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]


@admin.register(Menus)
class AdminMenus(ImportExportActionModelAdmin, admin.ModelAdmin):
    """
    Custom admin configuration for the 'Menus' model.
    """
    search_fields = ['name', 'group__name']
    list_filter = ['active','group','parent']

    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MasterLookUp)    
class MasterLookUpAdmin(ImportExportModelAdmin, ImportExportFormat):
    def get_list_display(self, request):
        """
        Customize the list display for the admin page.
        """
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserProfile)    
class UserProfileAdmin(ImportExportModelAdmin, ImportExportFormat):
    list_display = ['user']
    
# from django.apps import apps

# # Get all models in the project
# all_models = apps.get_models()

# # Loop through the models and register only those that are not already registered
# for model in all_models:
#     try:
#         admin.site.register(model)
#     except admin.sites.AlreadyRegistered:
#         pass