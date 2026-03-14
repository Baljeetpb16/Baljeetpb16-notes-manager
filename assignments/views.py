from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AssignmentFilterForm, AssignmentForm
from .models import Assignment


@login_required
def assignment_list(request):
    form = AssignmentFilterForm(request.GET or None)
    assignments = Assignment.objects.filter(created_by=request.user)

    if form.is_valid():
        status = form.cleaned_data.get("status")
        subject = form.cleaned_data.get("subject")
        if status:
            assignments = assignments.filter(status=status)
        if subject:
            assignments = assignments.filter(subject=subject)

    return render(
        request,
        "assignments/list.html",
        {"assignments": assignments, "form": form},
    )


@login_required
def assignment_add(request):
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            return redirect("assignments:list")
    else:
        form = AssignmentForm()
    return render(request, "assignments/form.html", {"form": form, "action": "Add"})


@login_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return redirect("assignments:list")
    else:
        form = AssignmentForm(instance=assignment)
    return render(request, "assignments/form.html", {"form": form, "action": "Edit"})


@login_required
def assignment_mark_done(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    assignment.status = "done"
    assignment.save()
    return redirect("assignments:list")


@login_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    if request.method == "POST":
        assignment.delete()
        return redirect("assignments:list")
    return render(request, "assignments/confirm_delete.html", {"assignment": assignment})
