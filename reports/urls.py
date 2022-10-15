from django.urls import path, include
from .views import custom_report, custom_report_reload, get_district, get_shelterhome


app_name = "reports"
urlpatterns = [
    path('report/<page_slug>/', custom_report, name="custom_report"),
    path('ajax/custom_report_reload/<page_slug>/<report_slug>/', custom_report_reload, name="custom_report_reload"),
    path('ajax/report_district/', get_district, name="get_district"),
    path('ajax/report_shelterhome/', get_shelterhome, name="get_shelterhome"),
    #     path('adoption-inquiry-report/', adoption_inquiry_report,
    #          name="adoption_inquiry_report"),
    #     path('case-being-worked-on/', case_being_worked_on,
    #          name="case_being_worked_on"),
    #     path('status-and-stage-report/', status_and_stage_report_by_children,
    #          name="status_and_stage_report_by_children"),

]
