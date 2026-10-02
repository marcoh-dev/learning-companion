from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from .forms import GoalForm


class OwnGoalMixin(LoginRequiredMixin):
    """Limit a goal view to the signed-in user's goals; anyone else's goal is a 404."""

    def get_queryset(self):
        return self.request.user.goals.all()


class GoalListView(OwnGoalMixin, ListView):
    template_name = "goals/goal_list.html"

    def get_queryset(self):
        return super().get_queryset().order_by("-updated_at")


class GoalDetailView(OwnGoalMixin, DetailView):
    template_name = "goals/goal_detail.html"


class GoalCreateView(LoginRequiredMixin, CreateView):
    form_class = GoalForm
    template_name = "goals/goal_form.html"
