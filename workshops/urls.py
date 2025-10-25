from django.urls import path

from .views import WorkshopListAPIView

urlpatterns = [
    path("", WorkshopListAPIView.as_view(), name="workshops"),
]
