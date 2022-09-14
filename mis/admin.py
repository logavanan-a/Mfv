from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from mis.models import MissionIndicatorAchievement, Task, DataEntryRemark


@admin.register(MissionIndicatorAchievement)
class AdminMissionIndicatorAchievement(ImportExportActionModelAdmin,admin.ModelAdmin):
    exclude = ['response']
    search_fields = ['task__name']
    list_display = ('id', 'active', 'created', 'modified', 'listing_order', 'task', 'number_working_days', 'project_reference_file', 'camp_organized')
    # def get_list_display(self, request):
    #     return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Task)
class AdminTask(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['task_status']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(DataEntryRemark)
class AdminDataEntryRemark(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]