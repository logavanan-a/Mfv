from django.urls import path
from  .views import *

app_name = "mis"

urlpatterns = [
    path('login/', login_view, name="login"),

    path('mission/list/', mission_list, name="mission_list"),
    path('table_add/<id>/', missionindicator_table, name='table'),

    path('mission_form/list/', mission_form_list, name="mission_form_list"),
    path('generator_form/<id>/', generator_form, name='generator_form'),



    path('mission/add/', mission_add, name='adding')
	]
