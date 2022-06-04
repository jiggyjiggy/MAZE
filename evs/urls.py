from django.urls import path
from evs.views   import EVMapView, SearchNearestEVView, EVAdminView

urlpatterns = [
    path("", EVMapView.as_view()),
    path("/nearest", SearchNearestEVView.as_view()),
    path("/admin", EVAdminView.as_view())
]