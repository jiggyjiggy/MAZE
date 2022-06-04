from django.urls import path
from cafes.views import CafeMapView, SearchNearestCafeView

urlpatterns = [
    path("", CafeMapView.as_view()),
    path("/nearest", SearchNearestCafeView.as_view())
]