from django import forms

from .models import Note, Subject


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "subject", "tags", "file", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "exam, important, unit1"}
            ),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "visibility": forms.Select(attrs={"class": "form-select"}),
        }


class NoteFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Search title or tags…"}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All subjects",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    semester = forms.IntegerField(
        required=False,
        label="Semester",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 8}),
    )
    visibility = forms.ChoiceField(
        choices=[("", "All"), ("private", "Private"), ("public", "Public")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
