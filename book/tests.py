from django.test import TestCase
from book.models import Book
from user.models import User
from django.core.exceptions import ValidationError


class BookModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverChoices.HARD,
            inventory=10,  # Adjust initial inventory
            daily_fee=1.50,
        )

    def test_book_str(self):
        self.assertEqual(str(self.book), self.book.title)

    def test_cover_choices(self):
        book_with_hard_cover = Book.objects.create(
            title="Hard Cover Book",
            author="Author A",
            cover=Book.CoverChoices.HARD,
            inventory=5,
            daily_fee=2.00,
        )
        book_with_soft_cover = Book.objects.create(
            title="Soft Cover Book",
            author="Author B",
            cover=Book.CoverChoices.SOFT,
            inventory=5,
            daily_fee=1.00,
        )
        self.assertEqual(book_with_hard_cover.cover, Book.CoverChoices.HARD)
        self.assertEqual(book_with_soft_cover.cover, Book.CoverChoices.SOFT)

    def test_inventory_update(self):
        self.book.inventory -= 1
        self.book.save()
        self.assertEqual(self.book.inventory, 9)

        self.book.inventory += 2
        self.book.save()
        self.assertEqual(self.book.inventory, 11)

        self.book.inventory = -1
        with self.assertRaises(ValidationError):
            self.book.full_clean()  # Use full_clean to trigger model validation
            self.book.save()

    def test_daily_fee(self):
        self.assertEqual(self.book.daily_fee, 1.50)

        # Test updating daily fee
        self.book.daily_fee = 2.00
        self.book.save()
        self.assertEqual(self.book.daily_fee, 2.00)
