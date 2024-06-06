from django.urls import path
from . views import *

app_name = "application_master"

urlpatterns = [
    path('list/<model>/', master_list_form),
    path('add/<model>/', master_add_form),
    path('edit/<model>/<id>/', master_edit_form),
    path('<model>/<id>/delete/', delete_record,name='delete_record'),
    path('details/<model>/<id>/', master_details_form),
    path('vendor_partner_user_mapping/<vendor_partner_id>/<model>/', vendor_partner_user_mapping, name="vendor_partner_user_mapping"),
    path('partner_mission_mapping_list/<partner_id>/', partner_mission_mapping_list, name="partner_mission_mapping_list"),
    path('partner_mission_mapping/<partner_id>/', partner_mission_mapping, name="partner_mission_mapping"),
    path('project_donor_mapping_list/<project_id>/', project_donor_mapping_list, name="project_donor_mapping_list"),
    path('project_donor_mapping/<project_id>/', project_donor_mapping, name="project_donor_mapping"),

	]