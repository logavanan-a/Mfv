from django.contrib import admin
from import_export import fields
from reports.models import ReportMeta, QuietlyReport
from import_export.admin import ImportExportActionModelAdmin



@admin.register(ReportMeta)
class ReportMetaAdmin(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Customizes the administration interface for the ReportMeta model.
    """
    list_display = ['report_title', 'page_slug', 'report_slug',
                    'display_order', 'active']
    fields = ['page_slug', 'report_slug',  'report_title', 'report_header',
              'report_query', 'display_order', 'filter_info', 'sort_info', 'custom_export_header', 'active']
    list_filter = ['report_title', 'report_slug']
    search_fields = ['report_title', 'report_slug']

@admin.register(QuietlyReport)
class QuietlyReportAdmin(ImportExportActionModelAdmin,admin.ModelAdmin):
    """
    Customizes the administration interface for the ReportMeta model.
    """
    list_display = ['project','indicator','academic_year','annual_target','q1_target','q2_target','q3_target','q4_target', 'active']
    fields = ['project','indicator','academic_year','annual_target','q1_target','q2_target','q3_target','q4_target', 'active']
    search_fields = ['project']
    list_filter = ['indicator', 'academic_year']

    