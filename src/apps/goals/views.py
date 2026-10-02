from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GoalListView(LoginRequiredMixin, TemplateView):
    template_name = "goals/goal_list.html"
