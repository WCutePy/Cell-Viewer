from django.urls import path

from cellviewer.views import index, saved_jobs


urlpatterns = [
    path("", index.index, name="index"),
    path("input_data", index.input_data),
    path("dash_or_save", index.dash_or_save),
    path("saved_jobs", saved_jobs.saved_jobs),
    path("saved_jobs/<int:job_id>/", saved_jobs.display_job),
    path("delete_job/<int:job_id>/", saved_jobs.delete_job),
]