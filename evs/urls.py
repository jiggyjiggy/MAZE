from django.urls import path
from evs.views   import EVMapView, EVAdminView

urlpatterns = [
    path("", EVMapView.as_view()),
    path("/admin", EVAdminView.as_view())
]