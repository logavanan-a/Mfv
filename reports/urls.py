from django.urls import path
from reports.views import custom_report, custom_report_reload, get_indicator,reports_listing, get_project,export_reportcsv,custom_report_csv,get_district,get_school, quietly_report,get_donor_district,custom_report_donor

app_name = "reports"
urlpatterns = [
    path('reports/exportcsv/<slug:slug>/',export_reportcsv),
    path('reports/custom-reports/donor-report/',custom_report_donor),
    path('reports/', reports_listing, name="reports_listing"),
    # path('report/<page_slug>/', custom_report, name="custom_report"),
    path('ajax/custom_report_reload/<page_slug>/<report_slug>/', custom_report_reload, name="custom_report_reload"),
    path('ajax/report_indicator/', get_indicator, name="get_indicator"),
    path('ajax/report_district/', get_district, name="get_district"),
    path('reports/ajax/donor_district/', get_donor_district, name="get_donor_district"),
    path('ajax/report_project/', get_project, name="get_project"),
    path('ajax/report_school/', get_school, name="get_school"),
    path('reports/custom-report-csv/<int:report_id>/',custom_report_csv),
    path('quietly-report/',quietly_report),
    
]
