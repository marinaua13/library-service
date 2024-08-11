from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from payment.models import Payment
from borrow.models import Borrowing
from book.models import Book
from unittest.mock import patch

User = get_user_model()


class PaymentTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        # Create a book instance
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverChoices.HARD,
            inventory=5,
            daily_fee=1.50,
        )

        # Create a borrowing instance
        self.borrowing = Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date="2024-09-10"
        )

        # Create a payment instance
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            status=Payment.StatusChoices.PENDING,
            type=Payment.TypeChoices.PAYMENT,
            session_url="http://example.com/session",
            session_id="sess_123",
            money_to_pay=10.00,
        )

    def test_create_payment_session(self):
        url = reverse("payment:payments-list")
        data = {
            "borrowing": self.borrowing.id,
            "status": Payment.StatusChoices.PENDING,
            "type": Payment.TypeChoices.PAYMENT,
            "session_url": "http://example.com/session",
            "session_id": "sess_456",
            "money_to_pay": 15.00,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 2)

    def test_cancel_payment(self):
        url = reverse("payment:payment_cancel")
        data = {"session_id": self.payment.session_id}
        response = self.client.post(url, data, format="json")
        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)

    def test_payment_success(self):
        url = reverse("payment:payment_success")
        response = self.client.get(url, {"session_id": self.payment.session_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Payment.StatusChoices.PENDING)

    @patch("stripe.Webhook.construct_event")
    def test_payment_webhook_success(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": self.payment.session_id}},
        }

        url = reverse("payment:stripe-webhook")
        payload = {
            "id": "evt_1EXQWt2eZvKYlo2Cgo1lPKJY",
            "type": "checkout.session.completed",
            "data": {"object": {"id": self.payment.session_id}},
        }
        sig_header = "t=123456,v1=abcdef,v0=ghijkl"

        response = self.client.post(
            url, data=payload, format="json", HTTP_STRIPE_SIGNATURE=sig_header
        )
        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)

    @patch("stripe.Webhook.construct_event")
    def test_payment_webhook_failure(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "non_existent_session_id"}},  # does not exist ID
        }

        url = reverse("payment:stripe-webhook")
        payload = {
            "id": "evt_1EXQWt2eZvKYlo2Cgo1lPKJY",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "non_existent_session_id"}},
        }
        sig_header = "t=123456,v1=abcdef,v0=ghijkl"

        response = self.client.post(
            url, data=payload, format="json", HTTP_STRIPE_SIGNATURE=sig_header
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
