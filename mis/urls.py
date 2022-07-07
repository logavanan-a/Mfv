from django.urls import path
from  .views import *
from django.conf.urls.static import static


app_name = "mis"

urlpatterns = [
    path('', login_view, name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),

    path('mission-list/', mission_list, name="mission-list"),
    path('<slug:slug>/monthly-report/<task_id>/', missionindicator_table, name='mission_detail'),
    path('mission-indicator/edit/list/', mission_indicator_edit),
    path('table_edit/<slug:slug>/<id>/', missionindicator_table_edit),
    path('task-list/', task_list, name="task-list"),

    path('mission/target/<id>/', missionindicator_target),
    path('mission-target/list/', mission_target_edit),
    path('target_table_edit/<ids>/<id>/', missiontarget_table_edit),

    path('mission_form/list/', mission_form_list, name="mission_form_list"),
    path('generator_form/<id>/', generator_form, name='generator_form'),

    
	]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

