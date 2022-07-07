from django.urls import path
from  .views import *
from django.conf.urls.static import static


app_name = "mis"

urlpatterns = [
    path('login/', login_view, name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),

    path('mission-list/', mission_list, name="mission-list"),
    path('<slug:slug>/monthly-report/', missionindicator_table, name='mission_detail'),
    path('mission-indicator/edit/list/', mission_indicator_edit),
    path('table_edit/<ids>/<id>/', missionindicator_table_edit),

    path('mission/target/<id>/', missionindicator_target),
    path('mission-target/list/', mission_target_edit),
    path('target_table_edit/<ids>/<id>/', missiontarget_table_edit),

    path('mission_form/list/', mission_form_list, name="mission_form_list"),
    path('generator_form/<id>/', generator_form, name='generator_form'),

    path('task-list/', task_list, name="task-list"),

	]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

