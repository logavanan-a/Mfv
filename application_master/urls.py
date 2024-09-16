from django.urls import path
from . views import *

app_name = "application_master"

urlpatterns = [
    path('list/<model>/', master_list_form),
    path('list/<model>/import/', master_list_form,{'key': 'import'}),
    path('add/<model>/', master_add_form),
    path('edit/<model>/<id>/', master_edit_form),
    path('<model>/<id>/delete/', delete_record,name='delete_record'),
    path('user_mapping/<id>/<user_id>/', user_project_status_update,name='delete_record'),
    path('details/<model>/<id>/', master_details_form),
    path('vendor_partner_user_mapping/<vendor_partner_id>/<model>/', vendor_partner_user_mapping, name="vendor_partner_user_mapping"),
    path('partner_mission_mapping_list/<partner_id>/', partner_mission_mapping_list, name="partner_mission_mapping_list"),
    path('partner_mission_mapping/<partner_id>/', partner_mission_mapping, name="partner_mission_mapping"),
    path('project_donor_mapping_list/<project_id>/', project_donor_mapping_list, name="project_donor_mapping_list"),
    path('project_donor_mapping/<project_id>/', project_donor_mapping, name="project_donor_mapping"),
    path('partner_mission_status_update/<dpl_id>/', partner_mission_status_update, name="partner_mission_status_update"),
    path("edit_user_partner_project/<id>/<model>/", edit_user_partner_project, name="edit_user_partner_project"),
    path('ajax/district/<state_id>/', get_district, name='get_district'),
    path('ajax/project/<partner_id>/', get_project, name='get_project'),
    path('adding_project/<id>/', adding_project, name='adding_project'),
    
    path('android_login/',LoginAndroidView.as_view()),
    path('user/android/list/',UserlistAndroid.as_view()),

    # ajax for save the activity date
    path('save-activity/', save_activity, name='save-activity'),

	]