from django.db.models import Count, Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView, View

from .models import Announcement, Feedback, FunctionalGroup, LearningResource, Reaction, ReactionType, SyntheticRoute, Tag


class HomeView(TemplateView):
    template_name = "reactions/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_reactions"] = (
            Reaction.published.select_related("reaction_type").prefetch_related("tags").order_by("-updated_at")[:6]
        )
        context["featured_routes"] = SyntheticRoute.published.order_by("-updated_at")[:4]
        context["learning_resources"] = LearningResource.published.order_by("-updated_at")[:5]
        context["reaction_types"] = ReactionType.objects.all()[:12]
        context["tags"] = Tag.objects.all()[:12]
        context["announcements"] = Announcement.objects.filter(is_active=True)[:5]
        return context


class DeployGuideView(TemplateView):
    template_name = "reactions/deploy_guide.html"


class ReactionListView(ListView):
    model = Reaction
    template_name = "reactions/reaction_list.html"
    context_object_name = "reactions"
    paginate_by = 12

    def get_queryset(self):
        queryset = Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups")
        query = self.request.GET.get("q", "").strip()
        type_slug = self.request.GET.get("type", "").strip()
        tag_slug = self.request.GET.get("tag", "").strip()
        functional_group = self.request.GET.get("functional_group", "").strip()
        exam = self.request.GET.get("exam", "").strip()
        sort = self.request.GET.get("sort", "").strip()

        if query:
            queryset = queryset.filter(
                Q(name_zh__icontains=query)
                | Q(name_en__icontains=query)
                | Q(aliases__icontains=query)
                | Q(condition__icontains=query)
                | Q(summary__icontains=query)
                | Q(exam_tips__icontains=query)
            )
        if type_slug:
            queryset = queryset.filter(reaction_type__slug=type_slug)
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        if functional_group:
            queryset = queryset.filter(functional_groups__pk=functional_group)
        if exam == "1":
            queryset = queryset.filter(tags__slug__in=["exam-high-frequency", "postgraduate-exam-key"])

        queryset = queryset.distinct()
        if sort == "type":
            return queryset.order_by("reaction_type__sort_order", "reaction_type__id", "name_en", "name_zh")
        if sort == "updated":
            return queryset.order_by("-updated_at", "name_en", "name_zh")
        return queryset.order_by("name_en", "name_zh")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_type"] = self.request.GET.get("type", "").strip()
        context["selected_tag"] = self.request.GET.get("tag", "").strip()
        context["selected_functional_group"] = self.request.GET.get("functional_group", "").strip()
        context["exam_filter"] = self.request.GET.get("exam", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "name").strip() or "name"
        context["reaction_types"] = ReactionType.objects.all()
        context["tags"] = Tag.objects.all()
        context["functional_groups"] = FunctionalGroup.objects.all()
        context["reaction_index"] = self.object_list.order_by("name_en", "name_zh")[:120]
        context["recommended_reactions"] = Reaction.published.select_related("reaction_type").prefetch_related("tags")[
            :3
        ]
        return context


class ReactionDetailView(DetailView):
    model = Reaction
    template_name = "reactions/reaction_detail.html"
    context_object_name = "reaction"
    queryset = Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups", "routes")


class RouteListView(ListView):
    model = SyntheticRoute
    template_name = "reactions/route_list.html"
    context_object_name = "routes"
    paginate_by = 12

    def get_queryset(self):
        queryset = SyntheticRoute.published.prefetch_related("related_reactions").annotate(step_total=Count("steps"))
        query = self.request.GET.get("q", "").strip()
        difficulty = self.request.GET.get("difficulty", "").strip()
        sort = self.request.GET.get("sort", "").strip()

        if query:
            queryset = queryset.filter(
                Q(target_product__icontains=query)
                | Q(summary__icontains=query)
                | Q(source__icontains=query)
                | Q(related_reactions__name_zh__icontains=query)
                | Q(related_reactions__name_en__icontains=query)
            )
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        queryset = queryset.distinct()
        if sort == "steps":
            return queryset.order_by("-step_total", "target_product")
        if sort == "difficulty":
            return queryset.order_by("difficulty", "target_product")
        if sort == "updated":
            return queryset.order_by("-updated_at", "target_product")
        return queryset.order_by("target_product")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_difficulty"] = self.request.GET.get("difficulty", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "target").strip() or "target"
        context["difficulty_choices"] = SyntheticRoute.Difficulty.choices
        context["recommended_routes"] = SyntheticRoute.published.annotate(step_total=Count("steps")).order_by(
            "-updated_at"
        )[:3]
        return context


class RouteDetailView(DetailView):
    model = SyntheticRoute
    template_name = "reactions/route_detail.html"
    context_object_name = "route"
    queryset = SyntheticRoute.published.prefetch_related("related_reactions", "steps", "steps__related_reactions")


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
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(relative_path__icontains=query)
                | Q(source_folder__icontains=query)
            )
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


class FeedbackView(View):
    def post(self, request):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        content = request.POST.get("content", "").strip()
        if name and content:
            Feedback.objects.create(name=name, email=email, content=content)
        return redirect("home")
