from django.db import models
from django.utils import timezone

from book.models import Book
from user.models import User


class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    borrow_date = models.DateField(editable=False)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.borrow_date = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"
