from django.urls import path
from . views import *

app_name = "application_master"

urlpatterns = [
     path('android/list/',UserlistAndroid.as_view()),
	]