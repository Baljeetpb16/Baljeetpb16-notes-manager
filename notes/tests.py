from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
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


# ---------------------------------------------------------------------------
# file_parser tests
# ---------------------------------------------------------------------------


class FileParserTest(TestCase):
    def test_parse_txt_file(self):
        from .file_parser import parse_file

        mock_file = MagicMock()
        mock_file.name = "notes.txt"
        mock_file.read.return_value = b"Hello world"
        result = parse_file(mock_file)
        self.assertEqual(result, "Hello world")

    def test_unsupported_extension_raises(self):
        from .file_parser import parse_file

        mock_file = MagicMock()
        mock_file.name = "notes.pdf"
        with self.assertRaises(ValueError):
            parse_file(mock_file)


# ---------------------------------------------------------------------------
# api_integration tests
# ---------------------------------------------------------------------------


class ApiIntegrationTest(TestCase):
    @override_settings(HUGGINGFACE_API_KEY="")
    def test_missing_api_key_raises(self):
        from .api_integration import generate_questions_from_text

        with self.assertRaises(RuntimeError, msg="API key not configured"):
            generate_questions_from_text("some text")

    @override_settings(HUGGINGFACE_API_KEY="test-key")
    @patch("notes.api_integration.requests.post")
    def test_successful_response_returns_questions(self, mock_post):
        from .api_integration import generate_questions_from_text

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"generated_text": "1. What is photosynthesis?\n2. Explain osmosis?"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        questions = generate_questions_from_text("Plants use sunlight to make food.")
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    @override_settings(HUGGINGFACE_API_KEY="test-key")
    @patch("notes.api_integration.requests.post")
    def test_api_error_raises_runtime_error(self, mock_post):
        import requests as req

        from .api_integration import generate_questions_from_text

        mock_post.side_effect = req.RequestException("connection error")
        with self.assertRaises(RuntimeError):
            generate_questions_from_text("some text")

    def test_empty_text_returns_empty_list(self):
        from .api_integration import generate_questions_from_text

        # Must have a key set so we reach the trimming logic
        with override_settings(HUGGINGFACE_API_KEY="key"):
            with patch("notes.api_integration.requests.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = [{"generated_text": ""}]
                mock_response.raise_for_status.return_value = None
                mock_post.return_value = mock_response
                # Empty text is caught before the API call
                result = generate_questions_from_text("")
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# questions generator view tests
# ---------------------------------------------------------------------------


class GenerateQuestionsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quser", password="pass1234!")
        self.subject = Subject.objects.create(name="Biology", semester=1)
        self.client.login(username="quser", password="pass1234!")
        f = SimpleUploadedFile(
            "bio.txt", b"Plants use chlorophyll to absorb sunlight.", content_type="text/plain"
        )
        self.note = Note.objects.create(
            title="Bio Notes", subject=self.subject, file=f, uploaded_by=self.user
        )

    def test_get_page_renders(self):
        resp = self.client.get(reverse("notes:generate_questions", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Generate")

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("notes:generate_questions", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 302)

    @override_settings(HUGGINGFACE_API_KEY="test-key")
    @patch("notes.questions_generator.generate_questions_from_text")
    def test_post_returns_questions(self, mock_gen):
        mock_gen.return_value = ["What is chlorophyll?", "Explain photosynthesis?"]
        resp = self.client.post(reverse("notes:generate_questions", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "What is chlorophyll?")

    @override_settings(HUGGINGFACE_API_KEY="")
    def test_post_without_api_key_shows_error(self):
        resp = self.client.post(reverse("notes:generate_questions", args=[self.note.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "HUGGINGFACE_API_KEY")
