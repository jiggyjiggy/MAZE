from django.urls import path
from evs.views   import EVMapView

urlpatterns = [
    path("", EVMapView.as_view())
]