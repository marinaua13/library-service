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
from payment.service import calculate_fine, create_payment_session
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
        book = serializer.validated_data["book"]
        if book.inventory <= 0:
            raise ValidationError("The book is currently out of stock.")

        book.inventory -= 1
        book.save()

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

        # Set the actual return date
        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()

        # Update the book inventory
        borrowing.book.inventory += 1
        borrowing.book.save()

        # Calculate fine if the book is overdue
        fine = calculate_fine(borrowing)
        if fine > 0:
            create_payment_session(
                borrowing=borrowing,
                amount=fine,
                payment_type=Payment.TypeChoices.FINE,
                request=request,
            )

            return Response(
                {
                    "message": f"A fine of {fine} USD has been applied. Please pay using the provided session."
                },
                status=status.HTTP_200_OK,
            )

            # Return success message if no fine is due
        return Response(
            {"message": "Book returned successfully."}, status=status.HTTP_200_OK
        )
