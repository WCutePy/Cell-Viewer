from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("input_data", views.input_data, name="table")
]