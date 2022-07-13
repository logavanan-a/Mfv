from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget,
                                       Partner, PartnerMissionDonorMapping, State,
                                       UserPartnerMapping, Facility)

@admin.register(Menus)
class AdminMenus(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(State)
class AdminState(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(District)
class AdminDistrict(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Facility)
class AdminFacility(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorCategory)
class AdminMissionIndicatorCategory(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicator)
class AdminMissionIndicator(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Donor)
class AdminDonor(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(PartnerMissionDonorMapping)
class AdminPartnerMissionDonorMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Partner)
class AdminPartner(ImportExportActionModelAdmin,admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Mission)
class AdminMission(ImportExportActionModelAdmin,admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorTarget)
class AdminMissionIndicatorTarget(ImportExportActionModelAdmin,admin.ModelAdmin):
    # search_fields = ["name"]
    # list_filter = ('parent',"active")
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserPartnerMapping)
class AdminUserPartnerMapping(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

# @admin.register(UserPartnerMapping)
# class AdminUserPartnerMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
#     def get_list_display(self, request):
#         return [field.name for field in self.model._meta.concrete_fields]
