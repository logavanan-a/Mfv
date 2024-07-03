from django.urls import path
from survey.form_views import *

app_name = "survey"
urlpatterns = [
    path('list/<slug:survey_slug>/<str:key>/<int:project_id>/', WebResponseListing.as_view()),
    path('list/<slug:survey_slug>/', login_required(WebResponseListing.as_view(),login_url='/login/')),
    path('add-survey-form/<pk>/', add_survey_form),
    path('edit-survey-form/<survey_slug>/<creation_key>/', edit_survey_form),
    path('profile/<slug:survey_slug>/<creation_key>/', login_required(BackendResponseListing.as_view(),login_url='/login/')),#ProfilePage.as_view()
    path('profile/<creation_key>/', login_required(BackendResponseListing.as_view(),login_url='/login/')),#ProfilePage.as_view()

]