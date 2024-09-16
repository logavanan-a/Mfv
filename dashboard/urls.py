from django.urls import path
from dashboard.views import dashboard,monthly_dashboard_list,dashboard_data_approval,PartnerDistricts

app_name = "dashboard"
urlpatterns = [
    path('', dashboard, name="login"),
    path('weekly-dashboard/list/', monthly_dashboard_list),
    path('weekly-dashboard/<id>/', dashboard_data_approval),
    path('partner-districts/', PartnerDistricts.as_view()),
]