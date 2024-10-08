from django.urls import path, include
from rest_framework import routers

from borrow.views import BorrowingViewSet

app_name = "borrowing"

router = routers.DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowing")
urlpatterns = [
    path("", include(router.urls)),
]
