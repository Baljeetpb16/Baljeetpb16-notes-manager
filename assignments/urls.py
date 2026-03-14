from django.urls import path

from . import views

app_name = "assignments"

urlpatterns = [
    path("", views.assignment_list, name="list"),
    path("add/", views.assignment_add, name="add"),
    path("<int:pk>/edit/", views.assignment_edit, name="edit"),
    path("<int:pk>/done/", views.assignment_mark_done, name="mark_done"),
    path("<int:pk>/delete/", views.assignment_delete, name="delete"),
]
