from django import forms
from django.contrib.auth.models import User

from .models import Note, Subject


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "subject", "tags", "content", "file", "visibility"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "tags": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "exam, important, unit1"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Paste or type note text here (used for summarization and export)…",
                }
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


class NoteShareForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter username to share with…"}
        ),
        help_text="The username of the person you want to share this note with.",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f'No user found with username \u201c{username}\u201d.')

