from django.urls import path
from . views import *

urlpatterns = [
    path('userroles/android/role-types/list/', RoleTypesListAndroid.as_view()),
    path('user/android/list/',UserlistAndroid.as_view()),
	]