from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .exporter import export_docx, export_markdown, export_pdf
from .forms import NoteFilterForm, NoteForm, NoteShareForm
from .models import Note, NoteShare
from .questions_generator import generate_questions_for_note
from .summarizer import summarize


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
    shares = NoteShare.objects.filter(note=note).select_related("shared_with")
    return render(request, "notes/detail.html", {"note": note, "shares": shares})


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            return redirect("notes:detail", pk=note.pk)
    else:
        form = NoteForm(instance=note)
    return render(request, "notes/edit.html", {"form": form, "note": note})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    if request.method == "POST":
        note.file.delete(save=False)
        note.delete()
        return redirect("notes:list")
    return render(request, "notes/confirm_delete.html", {"note": note})


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------


@login_required
def note_summarize(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    summary = ""
    too_short = False
    if note.content:
        summary = summarize(note.content)
        # If the summarizer returned the full content unchanged, the text is too
        # short to condense further — surface this to the user.
        if summary and summary.strip() == note.content.strip():
            too_short = True
    return render(
        request,
        "notes/summarize.html",
        {"note": note, "summary": summary, "too_short": too_short},
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

_EXPORT_FORMATS = ("markdown", "pdf", "docx")


@login_required
def note_export(request, pk, fmt):
    if fmt not in _EXPORT_FORMATS:
        from django.http import Http404

        raise Http404("Unknown export format.")

    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)

    if fmt == "markdown":
        data = export_markdown(note)
        content_type = "text/markdown; charset=utf-8"
        filename = f"{note.title}.md"
    elif fmt == "pdf":
        data = export_pdf(note)
        content_type = "application/pdf"
        filename = f"{note.title}.pdf"
    else:  # docx
        data = export_docx(note)
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{note.title}.docx"

    response = HttpResponse(data, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Collaboration / Sharing
# ---------------------------------------------------------------------------


@login_required
def note_share(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    shares = NoteShare.objects.filter(note=note).select_related("shared_with")

    if request.method == "POST":
        form = NoteShareForm(request.POST)
        if form.is_valid():
            target_user = form.cleaned_data["username"]
            if target_user == request.user:
                messages.error(request, "You cannot share a note with yourself.")
            else:
                _, created = NoteShare.objects.get_or_create(note=note, shared_with=target_user)
                if created:
                    messages.success(request, f"Note shared with {target_user.username}.")
                else:
                    messages.info(request, f"Already shared with {target_user.username}.")
            return redirect("notes:share", pk=pk)
    else:
        form = NoteShareForm()

    return render(request, "notes/share.html", {"note": note, "form": form, "shares": shares})


@login_required
def note_unshare(request, pk, share_pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    share = get_object_or_404(NoteShare, pk=share_pk, note=note)
    if request.method == "POST":
        share.delete()
        messages.success(request, "Share removed.")
    return redirect("notes:share", pk=pk)


@login_required
def shared_note_detail(request, pk):
    """Read-only detail view for notes shared with the current user."""
    share = get_object_or_404(NoteShare, note__pk=pk, shared_with=request.user)
    return render(request, "notes/shared_note_detail.html", {"note": share.note})


@login_required
def shared_with_me(request):
    shares = (
        NoteShare.objects.filter(shared_with=request.user)
        .select_related("note__subject", "note__uploaded_by")
        .order_by("-shared_at")
    )
    return render(request, "notes/shared_with_me.html", {"shares": shares})


# ---------------------------------------------------------------------------
# Questions Generator
# ---------------------------------------------------------------------------


@login_required
def note_generate_questions(request, pk):
    note = get_object_or_404(Note, pk=pk, uploaded_by=request.user)
    questions = None
    error = None

    if request.method == "POST":
        try:
            questions = generate_questions_for_note(note)
        except (ValueError, RuntimeError) as exc:
            error = str(exc)

    return render(
        request,
        "notes/questions.html",
        {"note": note, "questions": questions, "error": error},
    )
