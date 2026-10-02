from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm
from .models import Profile


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request, f'Welcome, {self.object.get_username()}! Your account has been created.'
        )
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        # Always the requester's own profile; recreate it if it has gone missing.
        return Profile.objects.get_or_create(user=self.request.user)[0]

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been saved.')
        return super().form_valid(form)
