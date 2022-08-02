from django.conf.urls.static import static
from django.urls import path

from .views import *

app_name = "mis"

urlpatterns = [
    path('', login_view, name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),

    path('task-list/', task_list, name="task-list"),
    path('<slug:slug>/monthly-report/<task_id>/', missionindicator_add, name='mission_add'),
    path('mission_edit/<slug:slug>/<task_id>/<id>/', missionindicator_edit,name='mission_edit'),
    path("ajax-task/<task_id>", task_status_changes, name="submitted_approval"),

    path('project-list/', project_list, name="project-list"),
    path('project-add/', ProjectAdd.as_view(), name='project-add'),
    path('project-edit/<id>/', ProjectUpdate.as_view(), name='project-edit'),

    path("user_listing/", user_listing, name="user_listing"),
    path("user-add/", add_user, name="add_user"),
    path("user-profile/<id>/", user_profile, name="user_profile"),
    path("user-change-password/<id>/", user_change_password, name="user_change_password"),
    path("user-edit/<id>/", edit_user, name="edit_user"),
	]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

