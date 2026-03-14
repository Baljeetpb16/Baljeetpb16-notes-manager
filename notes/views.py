from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteFilterForm, NoteForm
from .models import Note


@login_required
def dashboard(request):
    note_count = Note.objects.filter(uploaded_by=request.user).count()
    recent_notes = Note.objects.filter(uploaded_by=request.user)[:5]

    from assignments.models import Assignment

    assignment_count = Assignment.objects.filter(created_by=request.user).count()
    pending_count = Assignment.objects.filter(created_by=request.user, status="pending").count()
    recent_assignments = Assignment.objects.filter(created_by=request.user)[:5]

    return render(
        request,
        "core/dashboard.html",
        {
            "note_count": note_count,
            "assignment_count": assignment_count,
            "pending_count": pending_count,
            "recent_notes": recent_notes,
            "recent_assignments": recent_assignments,
        },
    )


@login_required
def note_list(request):
    form = NoteFilterForm(request.GET or None)
    notes = Note.objects.filter(uploaded_by=request.user)

    if form.is_valid():
        q = form.cleaned_data.get("q")
        subject = form.cleaned_data.get("subject")
        semester = form.cleaned_data.get("semester")
        visibility = form.cleaned_data.get("visibility")

        if q:
            notes = notes.filter(Q(title__icontains=q) | Q(tags__icontains=q))
        if subject:
            notes = notes.filter(subject=subject)
        if semester:
            notes = notes.filter(subject__semester=semester)
        if visibility:
            notes = notes.filter(visibility=visibility)

    return render(request, "notes/list.html", {"notes": notes, "form": form})


@login_required
def note_add(request):
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = request.user
            note.save()
            return redirect("notes:detail", pk=note.pk)
    else:
        form = NoteForm()
    return render(request, "notes/add.html", {"form": form})


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    return render(request, "notes/detail.html", {"note": note})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    if request.method == "POST":
        note.file.delete(save=False)
        note.delete()
        return redirect("notes:list")
    return render(request, "notes/confirm_delete.html", {"note": note})
