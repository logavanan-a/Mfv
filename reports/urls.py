from django.urls import path
from reports.views import custom_report, custom_report_reload, get_indicator,reports_listing


app_name = "reports"
urlpatterns = [
    path('reports/', reports_listing, name="reports_listing"),
    path('report/<page_slug>/', custom_report, name="custom_report"),
    path('ajax/custom_report_reload/<page_slug>/<report_slug>/', custom_report_reload, name="custom_report_reload"),
    path('ajax/report_indicator/', get_indicator, name="get_indicator"),
]
