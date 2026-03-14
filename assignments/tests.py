from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.models import Subject

from .models import Assignment


class AssignmentModelTest(TestCase):
    def test_str(self):
        user = User.objects.create_user(username="u", password="pass!")
        subject = Subject.objects.create(name="CS", semester=1)
        a = Assignment(title="HW1", subject=subject, due_date="2025-12-31", created_by=user)
        self.assertEqual(str(a), "HW1")


class AssignmentViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234!")
        self.subject = Subject.objects.create(name="CS", semester=1)
        self.client.login(username="u1", password="pass1234!")

    def test_assignment_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("assignments:list"))
        self.assertRedirects(resp, "/accounts/login/?next=/assignments/")

    def test_assignment_list_authenticated(self):
        resp = self.client.get(reverse("assignments:list"))
        self.assertEqual(resp.status_code, 200)

    def test_assignment_add_get(self):
        resp = self.client.get(reverse("assignments:add"))
        self.assertEqual(resp.status_code, 200)

    def test_assignment_add_post(self):
        resp = self.client.post(
            reverse("assignments:add"),
            {
                "title": "My HW",
                "subject": self.subject.pk,
                "due_date": "2025-12-31",
                "status": "pending",
            },
        )
        self.assertRedirects(resp, reverse("assignments:list"))
        self.assertEqual(Assignment.objects.filter(created_by=self.user).count(), 1)

    def test_mark_done(self):
        a = Assignment.objects.create(
            title="HW2",
            subject=self.subject,
            due_date="2025-12-31",
            status="pending",
            created_by=self.user,
        )
        resp = self.client.post(reverse("assignments:mark_done", args=[a.pk]))
        self.assertRedirects(resp, reverse("assignments:list"))
        a.refresh_from_db()
        self.assertEqual(a.status, "done")

    def test_assignment_delete(self):
        a = Assignment.objects.create(
            title="HW3",
            subject=self.subject,
            due_date="2025-12-31",
            created_by=self.user,
        )
        resp = self.client.post(reverse("assignments:delete", args=[a.pk]))
        self.assertRedirects(resp, reverse("assignments:list"))
        self.assertFalse(Assignment.objects.filter(pk=a.pk).exists())
