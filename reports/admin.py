from django.contrib import admin
from import_export import fields
from reports.models import ReportMeta
from import_export.admin import ImportExportActionModelAdmin



@admin.register(ReportMeta)
class ReportMetaAdmin(ImportExportActionModelAdmin,admin.ModelAdmin):
    list_display = ['report_title', 'page_slug', 'report_slug',
                    'display_order', 'active']
    fields = ['page_slug', 'report_slug',  'report_title', 'report_header',
              'report_query', 'display_order', 'filter_info', 'sort_info', 'custom_export_header', 'active']
    list_filter = ['report_title', 'report_slug']
    search_fields = ['report_title', 'report_slug']
