from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from application_master.models import (District, Donor, Menus, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionIndicatorTarget,
                                       Partner, PartnerMissionDonorMapping, State,
                                       UserPartnerMapping, Facility,FacilityFiles)

@admin.register(Menus)
class AdminMenus(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['active']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

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

@admin.register(Facility)
class AdminFacility(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
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
    list_filter = ['category__name','indicator_type']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Donor)
class AdminDonor(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(PartnerMissionDonorMapping)
class AdminPartnerMissionDonorMapping(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['partner__name','mission__name','donor__name']
    list_filter = ['mission__name','donor__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Partner)
class AdminPartner(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name','slug']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Mission)
class AdminMission(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorTarget)
class AdminMissionIndicatorTarget(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['mission_indicator__name','facility__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserPartnerMapping)
class AdminUserPartnerMapping(admin.ModelAdmin):
    search_fields = ['partner__name','user__username']
    list_filter = ['active']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(FacilityFiles)
class AdminFacilityFiles(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name','facility__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
