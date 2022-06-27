from django.urls import path
from  .views import *

app_name = "mis"

urlpatterns = [
    path('login/', login_view, name="login"),
    path('child-list/', child_listing, name="child_list"),
    path('child-list/guardian-add/', guardian_add, name="guardian_add"),
    path('list/', indicator_list, name='screen_list'),
    path('mission/add/', mission_add, name='adding')
	]
