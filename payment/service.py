from datetime import datetime
from django.utils import timezone
import stripe
from django.conf import settings

from payment.models import Payment
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_total_price(borrowing):
    borrow_date = borrowing.borrow_date
    expected_return_date = borrowing.expected_return_date

    if isinstance(borrow_date, datetime):
        borrow_date = borrow_date.date()
    if isinstance(expected_return_date, datetime):
        expected_return_date = expected_return_date.date()

    days_borrowed = (expected_return_date - borrow_date).days
    daily_fee = borrowing.book.daily_fee

    return days_borrowed * daily_fee


def calculate_fine(borrowing):
    if not borrowing.expected_return_date:
        return 0

    overdue_days = (timezone.now().date() - borrowing.expected_return_date).days
    if overdue_days <= 0:
        return 0  # No fine if not overdue

    fine_per_day = 2  # This could be a configurable setting
    return overdue_days * fine_per_day


def create_payment_session(borrowing, amount, payment_type, request):
    success_url = (
        request.build_absolute_uri(reverse("payments:payment_success"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = (
        request.build_absolute_uri(reverse("payments:payment_cancel"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{payment_type.title()} for Borrowing {borrowing.id}",
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        borrowing=borrowing,
        status=Payment.StatusChoices.PENDING,
        type=payment_type,
        session_url=checkout_session.url,
        session_id=checkout_session.id,
        money_to_pay=amount,
    )

    return payment
