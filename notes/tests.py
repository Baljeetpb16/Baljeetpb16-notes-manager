
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Note, Subject


class SubjectModelTest(TestCase):
    def test_str(self):
        subject = Subject(name="Math", semester=1)
        self.assertEqual(str(subject), "Math (Sem 1)")


class NoteModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass1234!")
        self.subject = Subject.objects.create(name="Physics", semester=2)

    def test_tag_list(self):
        note = Note(title="N", subject=self.subject, tags="a, b, c", uploaded_by=self.user)
        self.assertEqual(note.tag_list(), ["a", "b", "c"])

    def test_tag_list_empty(self):
        note = Note(title="N", subject=self.subject, tags="", uploaded_by=self.user)
        self.assertEqual(note.tag_list(), [])


class NoteViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234!")
        self.subject = Subject.objects.create(name="Chem", semester=3)
        self.client.login(username="u1", password="pass1234!")

    def test_note_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("notes:list"))
        self.assertRedirects(resp, "/accounts/login/?next=/notes/")

    def test_note_list_authenticated(self):
        resp = self.client.get(reverse("notes:list"))
        self.assertEqual(resp.status_code, 200)

    def test_note_add_get(self):
        resp = self.client.get(reverse("notes:add"))
        self.assertEqual(resp.status_code, 200)

    def test_note_add_post(self):
        f = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        resp = self.client.post(
            reverse("notes:add"),
            {
                "title": "Test Note",
                "subject": self.subject.pk,
                "tags": "test",
                "file": f,
                "visibility": "private",
            },
        )
        self.assertEqual(Note.objects.filter(uploaded_by=self.user).count(), 1)
        note = Note.objects.first()
        self.assertRedirects(resp, reverse("notes:detail", args=[note.pk]))

    def test_note_detail_own(self):
        f = SimpleUploadedFile("x.txt", b"x")
        note = Note.objects.create(
            title="My Note", subject=self.subject, file=f, uploaded_by=self.user
        )
        resp = self.client.get(reverse("notes:detail", args=[note.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_note_detail_other_user_forbidden(self):
        other = User.objects.create_user(username="u2", password="pass5678!")
        f = SimpleUploadedFile("y.txt", b"y")
        note = Note.objects.create(
            title="Other Note", subject=self.subject, file=f, uploaded_by=other
        )
        resp = self.client.get(reverse("notes:detail", args=[note.pk]))
        self.assertEqual(resp.status_code, 404)
