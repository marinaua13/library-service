from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    PaymentSuccessView,
    stripe_webhook,
)

app_name = "payment"
router = DefaultRouter()
router.register("", PaymentViewSet, basename="payments")

urlpatterns = router.urls + [
    path("stripe/success/", PaymentSuccessView.as_view(), name="payment_success"),
    path(
        "payments/cancel/",
        PaymentViewSet.as_view({"post": "cancel"}),
        name="payment_cancel",
    ),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
]
