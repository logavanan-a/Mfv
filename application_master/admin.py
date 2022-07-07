from django.contrib import admin

from application_master.models import (District, Donor, Mission,
                                       MissionIndicator,
                                       MissionIndicatorCategory,
                                       MissionQuestion, Partner,
                                       PartnerMissionMapping, State,
                                       UserPartnerMapping, VisionCentre)

# from import_export.admin import ImportExportModelAdmin

@admin.register(State)
class AdminState(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(District)
class AdminDistrict(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Partner)
class AdminPartner(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Mission)
class AdminMission(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(PartnerMissionMapping)
class AdminPartnerMissionMapping(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Donor)
class AdminDonor(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicator)
class AdminMissionIndicator(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorCategory)
class AdminMissionIndicatorCategory(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionQuestion) 
class AdminMissionQuestion(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(UserPartnerMapping)
class AdminUserPartnerMapping(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(VisionCentre)
class AdminVisionCentre(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

# @admin.register(State)
# class StateAdmin(ImportExportModelAdmin):
#     list_display = ['name',]

# @admin.register(District)
# class DistrictAdmin(ImportExportModelAdmin):
#     list_display = ['name','state']

# @admin.register(Partner)
# class PartnerAdmin(ImportExportModelAdmin):
#     list_display = ['name','state']

# @admin.register(Mission)
# class MissionAdmin(ImportExportModelAdmin):
#     list_display = ['name','district']

# @admin.register(PartnerMissionMapping)
# class PartnerMissionMappingAdmin(ImportExportModelAdmin):
#     list_display = ['name',]

# @admin.register(Donor)
# class DonorAdmin(ImportExportModelAdmin):
#     list_display = ['name','Date_of_association']

# @admin.register(MissionIndicator)
# class MissionIndicatorAdmin(ImportExportModelAdmin):
#     list_display = ['name','mission']

# @admin.register(MissionIndicatorCategory)
# class MissionIndicatorCategoryAdmin(ImportExportModelAdmin):
#     list_display = ['name','category']




