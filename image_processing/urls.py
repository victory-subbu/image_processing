from django.urls import path
from .views import UploadCSV, CheckStatus

urlpatterns = [
    path('upload/', UploadCSV.as_view(), name='upload_csv'),
    path('status/<uuid:request_id>/', CheckStatus.as_view(), name='check_status'),
]