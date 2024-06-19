from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin, ImportExportMixin
from import_export.formats import base_formats

class ImportExportFormat(ImportExportMixin):
    def get_export_formats(self):
        formats = (base_formats.CSV, base_formats.XLSX, base_formats.XLS,)
        return [f for f in formats if f().can_export()]

    def get_import_formats(self):
        formats = (base_formats.CSV, base_formats.XLSX, base_formats.XLS,)
        return [f for f in formats if f().can_import()]
    




@admin.register(DataEntryLevel)
class DataEntryLevelAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass






@admin.register(Survey)
class SurveyAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Block)
class BlockAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Choice)
class ChoiceAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(JsonAnswer)
class JsonAnswerAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Media)
class MediaAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(SurveyDisplayQuestions)
class SurveyDisplayQuestionsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(ErrorLog)
class ErrorLogAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Language)
class LanguageAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(AppLoginDetails)
class AppLoginDetailsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(AppAnswerData)
class AppAnswerDataAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(DeviceDetails)
class DeviceDetailsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Version)
class VersionAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(SurveySkip)    
class SurveySkipAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(Validations)
class ValidationsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(QuestionValidation)
class QuestionValidationAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(SurveyLog)
class SurveyLogAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(AppLabel)
class AppLabelAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass


@admin.register(QuestionLanguageValidation)
class QuestionLanguageValidationAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass
@admin.register(Levels)
class LevelsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass
@admin.register(ProjectLevels)
class ProjectLevelsAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(VersionUpdate)
class VersionUpdateAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(ResponseFiles)
class ResponseFilesAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass

@admin.register(LanguageTranslationText)    
class LanguageTranslationTextAdmin(ImportExportModelAdmin, ImportExportFormat):
    pass