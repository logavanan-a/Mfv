from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from django.contrib.auth.models import User

from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget, Partner,
                                       PartnerMissionMapping, Project,
                                       ProjectDonorMapping, ProjectFiles,
                                       State, UserPartnerMapping,
                                       UserProjectMapping)


class MissionIndicatorCategoryInline(admin.TabularInline): #StackedInline
    model = MissionIndicatorCategory
    extra = 0

class UserInline(admin.TabularInline): #StackedInline
    model = User
    extra = 0

@admin.register(Mission)
class AdminMission(ImportExportActionModelAdmin,admin.ModelAdmin):
    exclude = ['mission_template']
    # list_display = ('name', 'short_description','slug')
    inlines = [MissionIndicatorCategoryInline]
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserProjectMapping)
class AdminUserProjectMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
    # inlines = [UserInline]
    search_fields = ['project__name',]
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

# @admin.register(Menus)
# class AdminMenus(ImportExportActionModelAdmin,admin.ModelAdmin):
#     search_fields = ['name']
#     list_filter = ['active']
#     def get_list_display(self, request):
#         return [field.name for field in self.model._meta.concrete_fields]

@admin.register(State)
class AdminState(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(District)
class AdminDistrict(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['state']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Project)
class AdminProject(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name', 'partner_mission_mapping__partner__name']
    list_filter = ['active']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorCategory)
class AdminMissionIndicatorCategory(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['mission__name','category_type']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicator)
class AdminMissionIndicator(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['category__name','indicator_type','category__mission__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Donor)
class AdminDonor(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(PartnerMissionMapping)
class AdminPartnerMissionMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['partner__name', 'mission__name']
    list_filter = ['mission__name', 'partner__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Partner)
class AdminPartner(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name','slug']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorTarget)
class AdminMissionIndicatorTarget(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['mission_indicator__name','project__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserPartnerMapping)
class AdminUserPartnerMapping(admin.ModelAdmin):
    search_fields = ['partner__name','user__username']
    list_filter = ['active']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]


        
# @admin.register(ProjectFiles)
# class AdminProjectFiles(ImportExportActionModelAdmin,admin.ModelAdmin):
#     search_fields = ['name','project__name']
#     def get_list_display(self, request):
#         return [field.name for field in self.model._meta.concrete_fields]

@admin.register(ProjectDonorMapping)
class AdminProjectDonorMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['donor__name','project__name']
    list_filter = ['donor__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
