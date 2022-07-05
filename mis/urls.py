from django.urls import path
from  .views import *
from django.conf.urls.static import static


app_name = "mis"

urlpatterns = [
    path('login/', login_view, name="login"),

    path('mission/list/', mission_list, name="mission_list"),
    path('table_add/<id>/', missionindicator_table, name='table'),
    path('mission-indicator/edit/list/', mission_indicator_edit),
    path('table_edit/<ids>/<id>/', missionindicator_table_edit),

    path('mission/target/<id>/', missionindicator_target),
    path('mission-target/list/', mission_target_edit),
    path('target_table_edit/<ids>/<id>/', missiontarget_table_edit),

    path('mission_form/list/', mission_form_list, name="mission_form_list"),
    path('generator_form/<id>/', generator_form, name='generator_form'),
    path('mission/add/', mission_add, name='adding')

	]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

