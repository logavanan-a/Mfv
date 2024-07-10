from django.urls import path, include

from survey.api_view import *
from survey.api_views_version3 import * 
from survey.api_views_version1 import add_survey_answers_version_1

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
    path('updated-tables/',updatedtables), 
    path('language-assessment-list/',
         languageassessmentlist, name="languageassessmentlist"),         
    path('v3/response/', new_responses_list_v3,name='new_response_v3'),
    path('v1/push/', add_survey_answers_version_1,name='add_survey_answers_version_1'),
    path('level/<int:level>/', get_levels),
    path('program-responses/', program_responses_list,
         name="programresponse_list"),
    path('activists-responses/', avtivist_group_responses,
         name='activistsresponse_list'),       
    path('masterlookup-details/', MasterlookupDetails.as_view()),
    path('language-block-list/',languageblocklist, name="languageblocklist"),          
    path('feederrorlog/', feed_error_log, name='feed_error_log'),
    path('project/configuration/details/',ProjectConfigurationDetails.as_view()),
    path('archivedresponses-list/',archive_responses_list,name='archive_api'),


    #Monthly dashboard data pull request
    path('monthly-dashboard/',MonthlyDashboardData.as_view(),name='archive_api'),

]