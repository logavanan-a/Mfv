from django.contrib import admin

from mis.models import (MissionIndicatorAchievement, MissionIndicatorTarget,
                        Task)


@admin.register(MissionIndicatorAchievement)
class AdminMissionIndicatorAchievement(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(MissionIndicatorTarget)
class AdminMissionIndicatorTarget(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]

@admin.register(Task)
class AdminTask(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in self.model._meta.concrete_fields]
