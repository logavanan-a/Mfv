from django.urls import path
from dashboard.views import dashboard,monthly_dashboard_list,dashboard_data_approval

app_name = "dashboard"
urlpatterns = [
    path('', dashboard, name="login"),
    path('monthly-dashboard/list/', monthly_dashboard_list),
    path('monthly-dashboard/<id>/', dashboard_data_approval),
]