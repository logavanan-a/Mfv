from django.urls import path
from reports.views import custom_report, custom_report_reload, get_indicator,reports_listing, get_project,export_reportcsv,custom_report_csv,get_district,get_school,get_donor_district,custom_report_donor,get_partner_district,quarterly_report

app_name = "reports"
urlpatterns = [
    path('reports/exportcsv/<slug:slug>/',export_reportcsv),
    path('reports/custom-reports/performance-tracker/',custom_report_donor),
    path('reports/', reports_listing, name="reports_listing"),
    path('report/<page_slug>/', custom_report, name="custom_report"),
    path('ajax/custom_report_reload/<page_slug>/<report_slug>/', custom_report_reload, name="custom_report_reload"),
    path('ajax/report_indicator/', get_indicator, name="get_indicator"),
    path('ajax/report_district/', get_district, name="get_district"),
    path('reports/ajax/donor_district/', get_donor_district, name="get_donor_district"),
    path('reports/ajax/partner_district/', get_partner_district, name="get_partner_district"),
    path('ajax/report_project/', get_project, name="get_project"),
    path('ajax/report_school/', get_school, name="get_school"),
    path('reports/custom-report-csv/<int:report_id>/',custom_report_csv),
    path('quarterly-report/',quarterly_report),
    
]
