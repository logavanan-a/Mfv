from django.urls import path, include

from survey.api_view import *

urlpatterns = [
    path('question-list/',questionlist, name="questionlist"),
    path('choice-list/',choicelist, name="choicelist"),
    path('survey-list/',surveylist, name="surveylist"),
    path('block-list/', blocklist,name="blocklist"),
]