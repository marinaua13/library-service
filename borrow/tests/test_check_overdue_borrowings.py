from django.test import TestCase
from unittest.mock import patch
from datetime import date, timedelta
from celery.result import EagerResult
from borrow.models import Borrowing, Book
from user.models import User
from borrow.tasks import check_overdue_borrowings


class CeleryTasksTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverChoices.HARD,
            inventory=5,
            daily_fee=1.50,
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() - timedelta(days=1),  # Overdue
        )

    @patch("borrow.tasks.send_telegram_message")
    def test_check_overdue_borrowings(self, mock_send_telegram_message):
        """Test that overdue borrowings are detected and notifications are sent."""
        mock_send_telegram_message.return_value = {"success": True}

        result = check_overdue_borrowings.apply()
        self.assertIsInstance(
            result, EagerResult
        )  # Check that the task ran synchronously

        self.assertTrue(mock_send_telegram_message.called)
        self.assertIn(
            "Borrowing overdue:\nBook: Test Book\nUser: user@example.com\nExpected Return Date:",
            mock_send_telegram_message.call_args[0][0],
        )

    @patch("borrow.tasks.send_telegram_message")
    def test_no_overdue_borrowings(self, mock_send_telegram_message):
        """Test that no notifications are sent when there are no overdue borrowings."""
        # Change the expected return date to a future date
        self.borrowing.expected_return_date = date.today() + timedelta(days=1)
        self.borrowing.save()

        result = check_overdue_borrowings.apply()
        self.assertIsInstance(
            result, EagerResult
        )  # Check that the task ran synchronously

        # Check that the 'no overdue borrowings' message was sent
        mock_send_telegram_message.assert_called_with("No borrowings overdue today!")
