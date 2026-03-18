from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("add/", views.note_add, name="add"),
    path("shared-with-me/", views.shared_with_me, name="shared_with_me"),
    path("shared/<int:pk>/", views.shared_note_detail, name="shared_note_detail"),
    path("<int:pk>/", views.note_detail, name="detail"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
    path("<int:pk>/summarize/", views.note_summarize, name="summarize"),
    path("<int:pk>/export/<str:fmt>/", views.note_export, name="export"),
    path("<int:pk>/share/", views.note_share, name="share"),
    path("<int:pk>/share/<int:share_pk>/remove/", views.note_unshare, name="unshare"),
]
