from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from borrow.models import Borrowing
from borrow.serializers import (
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)
from borrow.telegram_utils import send_telegram_message
from payment.models import Payment
from payment.service import calculate_fine
from payment.views import CreatePaymentSessionView


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        elif self.action == "return_book":
            return BorrowingReturnSerializer
        elif self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        user = self.request.user

        # Admin can see all borrowings
        if user.is_staff:
            return queryset

        # non-staff users can see only active borrowings
        return queryset.filter(user=user, actual_return_date__isnull=True)

    def perform_create(self, serializer):
        user = self.request.user
        active_borrowings = Borrowing.objects.filter(
            user=user, actual_return_date__isnull=True
        )

        if active_borrowings.exists():
            raise ValidationError(
                "You already have an active borrowing. Please return the current book before borrowing a new one."
            )
        instance = serializer.save(user=user)
        message = f"New borrowing created:\nUser: {instance.user.id}\nUser: {instance.user.email}\nBook: {instance.book.title}"
        result = send_telegram_message(message)
        if not result["success"]:
            print(f"Failed to send Telegram message: {result['message']}")

        payment_view = CreatePaymentSessionView.as_view()
        request = self.request._request
        response = payment_view(request, pk=instance.id)

        if response.status_code != 200:
            instance.delete()
            raise ValidationError("Failed to create Stripe payment session.")
        return instance

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            return Response(
                {"error": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {"actual_return_date": timezone.now().date()}
        serializer = self.get_serializer(borrowing, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            borrowing.book.inventory += 1
            borrowing.book.save()

            # Calculating Fine
            fine = calculate_fine(borrowing)
            if fine > 0:
                Payment.objects.create(
                    borrowing=borrowing,
                    status=Payment.StatusChoices.PENDING,
                    type=Payment.TypeChoices.FINE,
                    # session_url="",  # Створіть сесію Stripe для штрафу, якщо потрібно
                    # session_id="",  # Створіть сесію Stripe для штрафу, якщо потрібно
                    money_to_pay=fine,
                )

                message = f"Book '{borrowing.book.title}' has been returned by {borrowing.user.email}. A fine of ${fine} has been issued for overdue."
                send_telegram_message(message)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
