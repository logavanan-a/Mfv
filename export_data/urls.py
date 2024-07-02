from django.urls import path
from .views import download_file
urlpatterns = [
    path('export_data/file-download/',download_file),
]
