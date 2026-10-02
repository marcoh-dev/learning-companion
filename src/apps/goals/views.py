from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView


class GoalListView(LoginRequiredMixin, ListView):
    template_name = "goals/goal_list.html"

    def get_queryset(self):
        return self.request.user.goals.all()
