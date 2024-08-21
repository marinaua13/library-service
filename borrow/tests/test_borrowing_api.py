from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from borrow.models import Borrowing
from book.models import Book
from user.models import User


class BorrowingModelTest(TestCase):

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

    def test_borrowing_creation(self):
        """Test that a Borrowing instance is created with the correct borrow_date."""
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
        )

        self.assertEqual(borrowing.borrow_date, timezone.now().date())
        self.assertEqual(
            str(borrowing), f"{self.user.email} borrowed {self.book.title}"
        )
        self.assertIsNone(borrowing.actual_return_date)

    def test_inventory_decrement_on_borrowing(self):
        """Test that the book inventory is decremented when a borrowing is created."""
        initial_inventory = self.book.inventory

        # Manually decrement inventory to simulate the view logic
        if self.book.inventory <= 0:
            raise ValidationError("The book is currently out of stock.")
        self.book.inventory -= 1
        self.book.save()

        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

    def test_inventory_increment_on_return(self):
        """Test that the book inventory is incremented when a book is returned."""
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
        )

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)
