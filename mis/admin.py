from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from mis.models import MissionIndicatorAchievement, Task


@admin.register(MissionIndicatorAchievement)
class AdminMissionIndicatorAchievement(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Task)
class AdminTask(ImportExportActionModelAdmin,admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
