from django.urls import path

from apps.cellviewer.views import index, saved_jobs


urlpatterns = [
    path("", index.index, name="index"),
    path("input_data", index.input_data),
    path("load_dash", index.load_dash),
    path("save_job", index.save_job),
    path("saved_jobs", saved_jobs.saved_jobs),
    path("saved_jobs/<int:job_id>/", saved_jobs.display_job),
    path("delete_job/<int:job_id>/", saved_jobs.delete_job),
]