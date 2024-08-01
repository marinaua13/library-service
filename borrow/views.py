from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from borrow.models import Borrowing
from borrow.serializers import (
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()

    # def perform_create(self, serializer):
    #     borrowing = serializer.save()
    #     borrowing.book.inventory -= 1  # Decrement inventory
    #     borrowing.book.save()

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        elif self.action == "return_book":
            return BorrowingReturnSerializer
        elif self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        book = borrowing.book
        # if book.inventory >= (book.borrowings.count() + book.inventory):
        #     return Response(
        #         {"error": "Inventory cannot exceed initial count."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        data = {"actual_return_date": timezone.now().date()}
        serializer = self.get_serializer(borrowing, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            # Update the book's inventory
            borrowing.book.inventory += 1
            borrowing.book.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
