from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt


from borrow.models import Borrowing
from .models import Payment
from .serializers import PaymentSerializer

from django.http import HttpResponse
import stripe

from .service import calculate_total_price, create_payment_session

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_KEY


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(
            borrowing__user=user,
            status__in=[Payment.StatusChoices.PENDING, Payment.StatusChoices.PAID],
        )

    def filter_queryset(self, queryset):
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(
            borrowing__user=user,
            status__in=[Payment.StatusChoices.PENDING],
        )

    @action(detail=False, methods=["post"])
    def cancel(self, request):
        session_id = request.data.get("session_id")

        if not session_id:
            return Response(
                {"error": "Missing session_id parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.StatusChoices.PENDING
            payment.save()
            return Response(
                {"message": "Payment was canceled"}, status=status.HTTP_200_OK
            )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CreatePaymentSessionView(APIView):
    def post(self, request, pk):
        borrowing = get_object_or_404(Borrowing, pk=pk)
        money_to_pay = calculate_total_price(borrowing)

        try:
            # Call the service function to create the payment session
            checkout_session = create_payment_session(
                borrowing=borrowing,
                amount=money_to_pay,
                payment_type=Payment.TypeChoices.PAYMENT,
                request=request,
            )

            # Now `checkout_session` contains the session information returned by Stripe
            return Response({"session_id": checkout_session.id})
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_KEY

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Process event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        try:
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.StatusChoices.PAID
            payment.save()

            # Return a response to Stripe to acknowledge receipt of the event
            return HttpResponse(status=200)

        except Payment.DoesNotExist:
            return HttpResponse(status=404)

    return HttpResponse(status=200)


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
            return Response(
                {
                    "message": "Payment status",
                    "session_id": session_id,
                    "status": payment.status,
                },
                status=status.HTTP_200_OK,
            )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )
