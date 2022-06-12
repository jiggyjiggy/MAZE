from django.urls import path
from commons.views import ParentTableView

urlpatterns = [
    path("", ParentTableView.as_view())
]