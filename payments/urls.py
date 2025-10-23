from django.urls import path
from . import views

urlpatterns = [
    path("purchased/", views.PurchasedItemsView.as_view(), name="purchased"),
    path("price/", views.PriceView.as_view(), name="price"),
    path("discount/", views.DiscountView.as_view(), name="discount"),
    path("pay/", views.PaymentView.as_view(), name="pay"),
    path("callback/", views.CallbackView.as_view(), name="callback"),
]
