from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from mis.models import MissionIndicatorAchievement, Task


@admin.register(MissionIndicatorAchievement)
class AdminMissionIndicatorAchievement(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['task__name']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Task)
class AdminTask(ImportExportActionModelAdmin,admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['task_status']
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
