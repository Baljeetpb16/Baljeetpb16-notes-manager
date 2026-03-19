from django import forms

from notes.models import Subject

from .models import Assignment


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "subject", "due_date", "status", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class AssignmentFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "All statuses"), ("pending", "Pending"), ("done", "Done")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All subjects",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
