from django.urls import path, include

from survey.api_view import *
from survey.api_views_version3 import * 

urlpatterns = [
    path('app-login/', applogin,name='app_login'),
    path('question-list/',questionlist, name="questionlist"),
    path('choice-list/',choicelist, name="choicelist"),
    path('survey-list/',surveylist, name="surveylist"),
    path('block-list/', blocklist,name="blocklist"),
    path('language-list/', languagelist),
    path('language-question-list/',
         languagequestionlist, name="languagequestionlist"),
    path('get-language-labels/', get_language_app_label,
                    name="get_language_app_label"),
    path('language-choice/',
         languagechoice, name="languagechoice"),
    path('assessment-list/',
         assessmentlist, name="assessmentlist"), 
    path('language-assessment-list/',
         languageassessmentlist, name="languageassessmentlist"),         
    path('v3/response/', new_responses_list_v3,name='new_response_v3'),
    path('level/<int:level>/', get_levels),
]