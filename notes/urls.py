from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("add/", views.note_add, name="add"),
    path("<int:pk>/", views.note_detail, name="detail"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
    path("<int:pk>/questions/", views.note_generate_questions, name="generate_questions"),
]
