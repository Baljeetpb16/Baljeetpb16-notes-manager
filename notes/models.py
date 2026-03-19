from django.contrib.auth.models import User
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["semester", "name"]
        unique_together = [("name", "semester")]

    def __str__(self):
        return f"{self.name} (Sem {self.semester})"


class Note(models.Model):
    VISIBILITY_CHOICES = [
        ("private", "Private"),
        ("public", "Public"),
    ]

    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="notes")
    tags = models.CharField(
        max_length=300,
        blank=True,
        help_text="Comma-separated tags, e.g. exam,important",
    )
    content = models.TextField(
        blank=True,
        help_text="Optional text content for summarization and export.",
    )
    file = models.FileField(upload_to="notes/%Y/%m/", blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="private")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class NoteShare(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="shares")
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_notes")
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("note", "shared_with")]
        ordering = ["-shared_at"]

    def __str__(self):
        return f"{self.note.title} → {self.shared_with.username}"
