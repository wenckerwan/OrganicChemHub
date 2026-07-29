"""User auth, registration, and profile views."""
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from ..models import Favorite, Feedback, StudyNote, StudyProgress


class RegisterView(TemplateView):
    template_name = "registration/register.html"

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            from django.shortcuts import redirect
            return redirect("home")
        return self.render_to_response({"form": form})

    def get(self, request, *args, **kwargs):
        return self.render_to_response({"form": UserCreationForm()})


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "reactions/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["favorites"] = Favorite.objects.filter(user=user).select_related("reaction", "route").order_by("-created_at")
        context["favorites_count"] = context["favorites"].count()
        context["notes"] = StudyNote.objects.filter(user=user).select_related("reaction", "route").order_by("-updated_at")
        context["notes_count"] = context["notes"].count()
        context["learned_count"] = StudyProgress.objects.filter(user=user, status=StudyProgress.Status.LEARNED).count()
        context["review_count"] = StudyProgress.objects.filter(user=user, status=StudyProgress.Status.REVIEW).count()
        context["user_feedbacks"] = Feedback.objects.filter(user=user).order_by("-created_at")
        return context
