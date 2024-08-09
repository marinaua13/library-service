from rest_framework import serializers

from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "status",
            "type",
            "session_url",
            "session_id",
            "money_to_pay",
        )


# class PaymentCancelSerializer(serializers.Serializer):
#     session_id = serializers.CharField(required=True)
#
#     class Meta:
#         model = Payment
#         fields = ("session_id",)
