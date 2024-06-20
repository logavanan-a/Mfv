from django.urls import path
from survey.views import *

app_name = "survey"
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
    path('import-modified-questions/<int:pk>/',ImportMQuestions.as_view())
]
