from django.urls import path
from survey.form_views import *

app_name = "survey"
urlpatterns = [
    path('list/<slug:survey_slug>/<str:school_creation_key>/<str:school_name>/', WebResponseListing.as_view()),
    path('list/<slug:survey_slug>/', login_required(WebResponseListing.as_view(),login_url='/login/')),
    path('add-survey-form/<pk>/', add_survey_form),
    path('edit-survey-form/<survey_slug>/<creation_key>/', edit_survey_form),
    path('profile/<slug:survey_slug>/<creation_key>/', login_required(WebResponseListing.as_view(),login_url='/login/')),#ProfilePage.as_view()
    path('profile/<creation_key>/', login_required(WebResponseListing.as_view(),login_url='/login/')),#ProfilePage.as_view()

    #Ajax call
    path('survey/location/', get_boundry_based_on_parentboundry),
    path('ajax/get_location/', get_location_boundry),
    path('ajax/district/<donor_id>/', get_donor_district),
    path('ajax/get_master_lookups/', get_master_lookups),


]