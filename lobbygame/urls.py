from django.urls import path
from . import views

urlpatterns = [
    path("status/", views.LobbygameStatusView.as_view(), name="lobby_game_status"),
    path(
        "discount-code/<str:uuid>/",
        views.LobbygameCreateDiscountView.as_view(),
        name="lobby_game_discount_code",
    ),
    path(
        "discount-code/with-request-uuid/<str:uuid>",
        views.LobbygameGetDiscount.as_view(),
        name="lobby_game_discount_code_get",
    ),
]
