from django.urls import path
from reports.views import custom_report, custom_report_reload, get_indicator,reports_listing


app_name = "reports"
urlpatterns = [
    path('reports/', reports_listing, name="reports_listing"),
    path('report/<page_slug>/', custom_report, name="custom_report"),
    path('ajax/custom_report_reload/<page_slug>/<report_slug>/', custom_report_reload, name="custom_report_reload"),
    path('ajax/report_indicator/', get_indicator, name="get_indicator"),
    # path('ajax/report_shelterhome/', get_shelterhome, name="get_shelterhome"),
    #     path('adoption-inquiry-report/', adoption_inquiry_report,
    #          name="adoption_inquiry_report"),
    #     path('case-being-worked-on/', case_being_worked_on,
    #          name="case_being_worked_on"),
    #     path('status-and-stage-report/', status_and_stage_report_by_children,
    #          name="status_and_stage_report_by_children"),

]
