"""Project URLconf with the goal list moved, to prove the nav reverses its URL by name."""
from django.urls import include, path

from config.urls import urlpatterns as project_urlpatterns

MOVED_GOAL_LIST_URL = "/elsewhere/goals/"

urlpatterns = [
    path("elsewhere/goals/", include("apps.goals.urls")),
    *(pattern for pattern in project_urlpatterns if str(pattern.pattern) != "goals/"),
]
