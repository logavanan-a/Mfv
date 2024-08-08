from django.urls import path
from survey.views import *
from survey.form_views import *

urlpatterns = [
    path('survey/', Surveys.as_view()),
    path('survey/add/', SurveyAdd.as_view()),
    path('survey/edit/<int:pk>/', SurveyEdit.as_view()),
    path('questions/<int:pk>/', SurveyQuestions.as_view()),
    path('question/add/<int:pk>/', AddSurveyQuestion.as_view()),
    path('question/edit/<int:pk>/', EditSurveyQuestion.as_view()),
    path('choices/<int:pk>/', QuestionChoices.as_view()),
    path('choice/add/<int:pk>/', AddQuestionChoice.as_view()),
    path('choice/edit/<int:pk>/', EditQuestionChoice.as_view()),
    path('skip-questions/<int:pk>/', SkipQuestionChoice.as_view()),
    path('import-questions/<int:pk>/', ImportQuestions.as_view()),
    path('import-modified-questions/<int:pk>/',ImportMQuestions.as_view()),
    path('survey/program-linkages/', ProgramRetreiveLinkages.as_view()),
    # path('list/<slug:survey_slug>/<str:key>/<int:project_id>/', WebResponseListing.as_view()),
    # path('list/<slug:survey_slug>/', login_required(WebResponseListing.as_view(),login_url='/login/')),
    #user and facility mapping api
    path('survey/ajax/get_custom_validation/', custom_validation_survey_wise_version1),

    # data import feature
    path('manage/generate-excel/<pk>/', generate_excel, name='generate_excel'),
    path('manage/activity/import/', SurveyResponseDataImport.as_view()),
    path('manage/activity/import-responses/<int:pk>/',ImportResponses.as_view()),
]
