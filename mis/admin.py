from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from mis.models import MissionIndicatorAchievement, Task, DataEntryRemark


@admin.register(MissionIndicatorAchievement)
class AdminMissionIndicatorAchievement(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Custom admin configuration for the 'MissionIndicatorAchievement' model.
    ImportExportActionModelAdmin provides the import/export functionality for the admin page.
    """
    search_fields = ['task__name']
    list_display = ('id', 'active', 'created', 'modified', 'listing_order', 'task', 'number_working_days', 'project_reference_file', 'camp_organized')

@admin.register(Task)
class AdminTask(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Custom admin configuration for the 'Task' model.
    ImportExportActionModelAdmin provides the import/export functionality for the admin page.
    """
    search_fields = ['name']
    list_filter = ['task_status']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(DataEntryRemark)
class AdminDataEntryRemark(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Custom admin configuration for the 'DataEntryRemark' model.
    ImportExportActionModelAdmin provides the import/export functionality for the admin page.
    """
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]