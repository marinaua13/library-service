from datetime import datetime
from django.utils import timezone
import stripe
from django.conf import settings

# from django.urls import reverse
# from .models import Payment

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
