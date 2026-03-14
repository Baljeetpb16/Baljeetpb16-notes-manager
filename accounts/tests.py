from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignupTest(TestCase):
    def test_signup_get(self):
        resp = self.client.get(reverse("accounts:signup"))
        self.assertEqual(resp.status_code, 200)

    def test_signup_post_creates_user(self):
        resp = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Str0ng!Pass",
                "password2": "Str0ng!Pass",
            },
        )
        self.assertRedirects(resp, "/")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_get(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)

    def test_login_post(self):
        User.objects.create_user(username="u", password="pass1234!")
        resp = self.client.post(
            reverse("accounts:login"), {"username": "u", "password": "pass1234!"}
        )
        self.assertRedirects(resp, "/")
