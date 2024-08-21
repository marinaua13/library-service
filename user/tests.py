from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse

User = get_user_model()


class UserTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.create_user_url = reverse("user:create")
        self.manage_user_url = reverse("user:manage")
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_create_user_successful(self):
        """Test creating a user with valid payload is successful"""
        payload = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(self.create_user_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], payload["email"])
        self.assertTrue("password" not in response.data)

    def test_create_user_existing_email(self):
        """Test creating a user that already exists fails"""
        response = self.client.post(self.create_user_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_invalid_email(self):
        """Test creating a user with an invalid email fails"""
        payload = {
            "email": "invalid-email",
            "password": "newpass123",
        }
        response = self.client.post(self.create_user_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for retrieving user"""
        response = self.client.get(self.manage_user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_successful(self):
        """Test retrieving profile for logged-in user"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.manage_user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        self.client.force_authenticate(user=self.user)
        payload = {"email": "updateduser@example.com", "password": "newpassword123"}

        response = self.client.patch(self.manage_user_url, payload)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))

    def test_update_user_invalid_email(self):
        """Test that updating user profile with invalid email fails"""
        self.client.force_authenticate(user=self.user)
        payload = {"email": "invalid-email"}

        response = self.client.patch(self.manage_user_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
