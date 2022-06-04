from django.urls import path
from evs.views   import EVMapView, SearchNearestEV,EVAdminView

urlpatterns = [
    path("", EVMapView.as_view()),
    path("/nearest", SearchNearestEV.as_view()),
    path("/admin", EVAdminView.as_view())
]