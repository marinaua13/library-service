from celery import shared_task
from datetime import date, timedelta

from .models import Borrowing
from .telegram_utils import send_telegram_message


@shared_task
def check_overdue_borrowings():
    today = date.today()
    tomorrow = today + timedelta(days=1)

    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=tomorrow, actual_return_date__isnull=True
    )

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"Borrowing overdue:\n"
                f"Book: {borrowing.book.title}\n"
                f"User: {borrowing.user.email}\n"
                f"Expected Return Date: {borrowing.expected_return_date}"
            )
            result = send_telegram_message(message)
            if not result["success"]:
                print(
                    f"Failed to send message for borrowing {borrowing.id}: {result['message']}"
                )
    else:
        send_telegram_message("No borrowings overdue today!")
