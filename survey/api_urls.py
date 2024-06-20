from django.urls import path, include

from survey.api_view import *

urlpatterns = [
    path('app-login/', applogin,name='app_login'),
    path('question-list/',questionlist, name="questionlist"),
    path('choice-list/',choicelist, name="choicelist"),
    path('survey-list/',surveylist, name="surveylist"),
    path('block-list/', blocklist,name="blocklist"),
    path('get-language-labels/', get_language_app_label,
                    name="get_language_app_label"),
]