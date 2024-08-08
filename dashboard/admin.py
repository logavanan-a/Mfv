from django.contrib import admin
from .models import *

# Register your models here.

# Register the DashboardSummaryLog model with the admin site
admin.site.register(DashboardSummaryLog)  
admin.site.register(DashboardWidgetTypes)  
admin.site.register(DashboardIndicatorFilter)  
admin.site.register(DashboardChartWidgets)  
admin.site.register(MonthlyDashboard)  
admin.site.register(Remarks)  

    
