from django.urls import path
from . views import *

app_name = "application_master"

urlpatterns = [
    path('userroles/android/role-types/list/', RoleTypesListAndroid.as_view()),
    path('user/android/list/',UserlistAndroid.as_view()),
	]