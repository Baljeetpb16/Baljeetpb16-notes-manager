from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
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


# ---------------------------------------------------------------------------
# summarize view tests
# ---------------------------------------------------------------------------


class AssignmentSummarizeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="su1", password="pass1234!")
        self.subject = Subject.objects.create(name="Math", semester=1)
        self.client.login(username="su1", password="pass1234!")
        self.assignment = Assignment.objects.create(
            title="Algebra HW",
            subject=self.subject,
            due_date="2025-12-31",
            status="pending",
            description="Solve chapters 3 and 4 from the textbook.",
            created_by=self.user,
        )

    def test_get_page_renders(self):
        resp = self.client.get(reverse("assignments:summarize", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Summarise")

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("assignments:summarize", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 302)

    @override_settings(HUGGINGFACE_API_KEY="test-key")
    @patch("assignments.views.summarize_text")
    def test_post_returns_summary(self, mock_summarize):
        mock_summarize.return_value = "Algebra homework due end of year."
        resp = self.client.post(reverse("assignments:summarize", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Algebra homework due end of year.")

    @override_settings(HUGGINGFACE_API_KEY="")
    def test_post_without_api_key_shows_error(self):
        resp = self.client.post(reverse("assignments:summarize", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "HUGGINGFACE_API_KEY")

    def test_other_user_gets_404(self):
        User.objects.create_user(username="su2", password="pass5678!")
        self.client.login(username="su2", password="pass5678!")
        resp = self.client.get(reverse("assignments:summarize", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 404)
