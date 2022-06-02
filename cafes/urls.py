from django.urls import path
from cafes.views import CafeMapView

urlpatterns = [
    path("", CafeMapView.as_view())
]