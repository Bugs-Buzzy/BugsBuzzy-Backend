from django.urls import path
from . import views

urlpatterns = [
    path('price/', views.PriceView.as_view(), name='price'),
    path('pay/', views.PaymentView.as_view(), name='pay'),
    path('callback/', views.CallbackView.as_view(), name='callback'),
]
