
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Note, NoteShare, Subject
from .summarizer import summarize


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


class NoteShareModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass1234!")
        self.other = User.objects.create_user(username="other", password="pass1234!")
        self.subject = Subject.objects.create(name="Bio", semester=1)
        self.note = Note.objects.create(
            title="Bio Notes", subject=self.subject, uploaded_by=self.owner
        )

    def test_str(self):
        share = NoteShare(note=self.note, shared_with=self.other)
        self.assertIn("Bio Notes", str(share))
        self.assertIn("other", str(share))


class SummarizerTest(TestCase):
    def test_empty_text(self):
        self.assertEqual(summarize(""), "")

    def test_short_text_returned_unchanged(self):
        text = "This is a short sentence. Here is another. And one more."
        result = summarize(text, num_sentences=3)
        self.assertEqual(result, text.strip())

    def test_summary_is_shorter_than_original(self):
        text = " ".join(
            [
                "Photosynthesis is the process by which plants convert sunlight into energy.",
                "Chlorophyll is the pigment that absorbs light in plant cells.",
                "The light-dependent reactions occur in the thylakoid membranes.",
                "The Calvin cycle takes place in the stroma of the chloroplast.",
                "Oxygen is released as a byproduct of photosynthesis.",
                "Carbon dioxide and water are the primary inputs for the reaction.",
                "Glucose produced during photosynthesis is used for plant growth.",
            ]
        )
        result = summarize(text, num_sentences=3)
        self.assertLess(len(result), len(text))

    def test_summary_sentence_count(self):
        text = " ".join(
            [
                "The mitochondria is the powerhouse of the cell.",
                "It produces ATP through cellular respiration.",
                "The inner membrane contains the electron transport chain.",
                "The matrix is where the Krebs cycle takes place.",
                "Mitochondria have their own DNA and ribosomes.",
            ]
        )
        result = summarize(text, num_sentences=2)
        sentence_count = len([s for s in result.split(". ") if s])
        self.assertLessEqual(sentence_count, 3)


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


class NoteSummarizeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234!")
        self.subject = Subject.objects.create(name="CS", semester=1)
        self.client.login(username="u1", password="pass1234!")
        self.note = Note.objects.create(
            title="CS Notes",
            subject=self.subject,
            content="Algorithms are step-by-step procedures for solving problems. "
            "Data structures organize data efficiently. "
            "Complexity analysis measures algorithm performance. "
            "Sorting algorithms order data in sequences. "
            "Graph algorithms solve connectivity problems.",
            uploaded_by=self.user,
        )

    def test_summarize_get(self):
        resp = self.client.get(reverse("notes:summarize", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("summary", resp.context)

    def test_summarize_no_content(self):
        note = Note.objects.create(
            title="Empty", subject=self.subject, uploaded_by=self.user
        )
        resp = self.client.get(reverse("notes:summarize", args=[note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["summary"], "")

    def test_summarize_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("notes:summarize", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 302)


class NoteExportViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234!")
        self.subject = Subject.objects.create(name="Math", semester=2)
        self.client.login(username="u1", password="pass1234!")
        self.note = Note.objects.create(
            title="Math Notes",
            subject=self.subject,
            content="Calculus involves derivatives and integrals.",
            uploaded_by=self.user,
        )

    def test_export_markdown(self):
        resp = self.client.get(reverse("notes:export", args=[self.note.pk, "markdown"]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/markdown", resp["Content-Type"])
        self.assertIn(b"Math Notes", resp.content)

    def test_export_pdf(self):
        resp = self.client.get(reverse("notes:export", args=[self.note.pk, "pdf"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_export_docx(self):
        resp = self.client.get(reverse("notes:export", args=[self.note.pk, "docx"]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("wordprocessingml", resp["Content-Type"])

    def test_export_invalid_format(self):
        resp = self.client.get(reverse("notes:export", args=[self.note.pk, "xyz"]))
        self.assertEqual(resp.status_code, 404)

    def test_export_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("notes:export", args=[self.note.pk, "markdown"]))
        self.assertEqual(resp.status_code, 302)


class NoteShareViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass1234!")
        self.other = User.objects.create_user(username="other", password="pass1234!")
        self.subject = Subject.objects.create(name="Bio", semester=1)
        self.note = Note.objects.create(
            title="Bio Notes", subject=self.subject, uploaded_by=self.owner
        )
        self.client.login(username="owner", password="pass1234!")

    def test_share_page_get(self):
        resp = self.client.get(reverse("notes:share", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_share_with_user(self):
        resp = self.client.post(
            reverse("notes:share", args=[self.note.pk]),
            {"username": "other"},
        )
        self.assertRedirects(resp, reverse("notes:share", args=[self.note.pk]))
        self.assertTrue(NoteShare.objects.filter(note=self.note, shared_with=self.other).exists())

    def test_share_duplicate_idempotent(self):
        self.client.post(reverse("notes:share", args=[self.note.pk]), {"username": "other"})
        self.client.post(reverse("notes:share", args=[self.note.pk]), {"username": "other"})
        self.assertEqual(NoteShare.objects.filter(note=self.note, shared_with=self.other).count(), 1)

    def test_share_with_self_rejected(self):
        resp = self.client.post(
            reverse("notes:share", args=[self.note.pk]),
            {"username": "owner"},
        )
        self.assertRedirects(resp, reverse("notes:share", args=[self.note.pk]))
        self.assertFalse(NoteShare.objects.filter(note=self.note, shared_with=self.owner).exists())

    def test_share_invalid_username(self):
        resp = self.client.post(
            reverse("notes:share", args=[self.note.pk]),
            {"username": "nonexistentuser"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(NoteShare.objects.filter(note=self.note).exists())

    def test_unshare(self):
        share = NoteShare.objects.create(note=self.note, shared_with=self.other)
        resp = self.client.post(reverse("notes:unshare", args=[self.note.pk, share.pk]))
        self.assertRedirects(resp, reverse("notes:share", args=[self.note.pk]))
        self.assertFalse(NoteShare.objects.filter(pk=share.pk).exists())

    def test_shared_with_me_list(self):
        NoteShare.objects.create(note=self.note, shared_with=self.other)
        self.client.logout()
        self.client.login(username="other", password="pass1234!")
        resp = self.client.get(reverse("notes:shared_with_me"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["shares"]), 1)

    def test_shared_note_detail(self):
        NoteShare.objects.create(note=self.note, shared_with=self.other)
        self.client.logout()
        self.client.login(username="other", password="pass1234!")
        resp = self.client.get(reverse("notes:shared_note_detail", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["note"], self.note)

    def test_shared_note_detail_non_recipient_forbidden(self):
        User.objects.create_user(username="third", password="pass1234!")
        self.client.logout()
        self.client.login(username="third", password="pass1234!")
        resp = self.client.get(reverse("notes:shared_note_detail", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 404)


