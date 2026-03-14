from django.contrib import admin

from .models import Note, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "semester"]
    list_filter = ["semester"]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "visibility", "uploaded_by", "created_at"]
    list_filter = ["visibility", "subject"]
    search_fields = ["title", "tags"]
