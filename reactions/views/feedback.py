"""Feedback, learning resources, and message views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView, View

from ..models import Feedback, LearningResource, Message


class FeedbackView(View):
    def post(self, request):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", Feedback.Category.OTHER)
        if name and content:
            Feedback.objects.create(
                name=name, email=email, content=content, category=category,
                user=request.user if request.user.is_authenticated else None,
            )
        return redirect("home")


class LearningResourceListView(ListView):
    model = LearningResource
    template_name = "reactions/learning_resource_list.html"
    context_object_name = "resources"
    paginate_by = 20

    def get_queryset(self):
        queryset = LearningResource.published.all()
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        has_answer = self.request.GET.get("has_answer", "").strip()
        sort = self.request.GET.get("sort", "").strip()

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(relative_path__icontains=query) | Q(source_folder__icontains=query))
        if category:
            queryset = queryset.filter(category=category)
        if has_answer == "1":
            queryset = queryset.filter(has_answer=True)
        if sort == "year":
            return queryset.order_by("-year", "title")
        if sort == "category":
            return queryset.order_by("category", "-year", "title")
        if sort == "size":
            return queryset.order_by("-size_bytes", "title")
        if sort == "updated":
            return queryset.order_by("-updated_at", "title")
        return queryset.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_category"] = self.request.GET.get("category", "").strip()
        context["has_answer"] = self.request.GET.get("has_answer", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "title").strip() or "title"
        context["category_choices"] = LearningResource.Category.choices
        context["recommended_resources"] = LearningResource.published.order_by("-updated_at")[:5]
        return context


class MessageListView(LoginRequiredMixin, ListView):
    template_name = "reactions/messages.html"
    context_object_name = "messages"
    paginate_by = 20

    def get_queryset(self):
        qs = Message.objects.filter(recipient=self.request.user)
        msg_type = self.request.GET.get("type", "").strip()
        if msg_type:
            qs = qs.filter(msg_type=msg_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_type"] = self.request.GET.get("type", "").strip()
        context["type_choices"] = Message.Type.choices
        return context


class MessageDetailView(LoginRequiredMixin, DetailView):
    template_name = "reactions/message_detail.html"
    context_object_name = "msg"

    def get_queryset(self):
        return Message.objects.filter(recipient=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read"])
        return obj


class MarkAllMessagesReadView(LoginRequiredMixin, View):
    def post(self, request):
        Message.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect("messages")
