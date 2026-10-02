from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import GoalForm
from .models import Goal


class OwnGoalMixin(LoginRequiredMixin):
    """Limit a goal view to the signed-in user's goals; anyone else's goal is a 404."""

    def get_queryset(self):
        return self.request.user.goals.all()


class GoalListView(OwnGoalMixin, ListView):
    template_name = "goals/goal_list.html"

    def active_status(self):
        """The requested ?status= if it is a known status, otherwise "" (no filter)."""
        status = self.request.GET.get("status", "")
        return status if status in Goal.Status.values else ""

    def get_queryset(self):
        goals = super().get_queryset().order_by("-updated_at")
        if status := self.active_status():
            goals = goals.filter(status=status)
        return goals


class GoalDetailView(OwnGoalMixin, DetailView):
    template_name = "goals/goal_detail.html"


class GoalCreateView(LoginRequiredMixin, CreateView):
    form_class = GoalForm
    template_name = "goals/goal_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, "Goal created.")
        return super().form_valid(form)


class GoalUpdateView(OwnGoalMixin, UpdateView):
    form_class = GoalForm
    template_name = "goals/goal_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Goal saved.")
        return super().form_valid(form)


class GoalDeleteView(OwnGoalMixin, DeleteView):
    template_name = "goals/goal_confirm_delete.html"
    success_url = reverse_lazy("goal-list")

    def form_valid(self, form):
        messages.success(self.request, "Goal deleted.")
        return super().form_valid(form)
