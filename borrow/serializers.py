from django.utils import timezone
from rest_framework import serializers

from book.serializers import BookSerializer
from borrow.models import Borrowing


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer()

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]


class BorrowingCreateSerializer(serializers.ModelSerializer):
    borrow_date = serializers.DateField(default=timezone.now().date, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Borrowing
        fields = ["user", "book", "borrow_date", "expected_return_date"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            if Borrowing.objects.filter(
                user=user, actual_return_date__isnull=True
            ).exists():
                raise serializers.ValidationError(
                    "You already have an active borrowing."
                )
        return attrs


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ["actual_return_date"]


class BorrowingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = [
            "id",
            "user",
            "book",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        ]
