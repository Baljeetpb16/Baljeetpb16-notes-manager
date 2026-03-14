from django.contrib import admin

from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "due_date", "status", "created_by"]
    list_filter = ["status", "subject"]
    search_fields = ["title"]
