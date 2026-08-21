"""Route list, detail, and note saving views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, View

from ..models import Favorite, FunctionalGroup, PublishStatus, RouteStep, StudyNote, StudyProgress, SyntheticRoute
from ..services.visits import increment_object_visit
from .mixins import CommentContextMixin


class RouteListView(ListView):
    model = SyntheticRoute
    template_name = "reactions/route_list.html"
    context_object_name = "routes"
    paginate_by = 12

    def get_queryset(self):
        queryset = SyntheticRoute.published.prefetch_related(
            "related_named_reactions",
            "related_general_reactions",
            "related_functional_groups",
        ).annotate(step_total=Count("steps"))
        query = self.request.GET.get("q", "").strip()
        difficulty = self.request.GET.get("difficulty", "").strip()
        functional_group = self.request.GET.get("functional_group", "").strip()
        sort = self.request.GET.get("sort", "").strip()

        if query:
            queryset = queryset.filter(
                Q(target_product__icontains=query) | Q(summary__icontains=query) | Q(source__icontains=query)
                | Q(related_named_reactions__name_zh__icontains=query)
                | Q(related_named_reactions__name_en__icontains=query)
                | Q(related_general_reactions__name_zh__icontains=query)
                | Q(related_general_reactions__name_en__icontains=query)
            )
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if functional_group:
            queryset = queryset.filter(related_functional_groups__name_en__iexact=functional_group)
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
        context["selected_functional_group"] = self.request.GET.get("functional_group", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "target").strip() or "target"
        context["difficulty_choices"] = SyntheticRoute.Difficulty.choices
        context["functional_group_choices"] = FunctionalGroup.objects.filter(routes__status=PublishStatus.PUBLISHED).distinct().order_by("name_zh")
        context["recommended_routes"] = SyntheticRoute.published.annotate(step_total=Count("steps")).order_by("-updated_at")[:3]
        return context


class RouteDetailView(CommentContextMixin, DetailView):
    model = SyntheticRoute
    template_name = "reactions/route_detail.html"
    context_object_name = "route"
    queryset = SyntheticRoute.published.prefetch_related(
        "related_named_reactions",
        "related_general_reactions",
        "related_functional_groups",
        "steps",
        "steps__related_named_reactions",
        "steps__related_general_reactions",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        route = self.object
        context["content_visit_stats"] = increment_object_visit(route)
        if user.is_authenticated:
            context["is_favorited"] = Favorite.objects.filter(user=user, route=route).exists()
            context["user_note"] = StudyNote.objects.filter(user=user, route=route).first()
            context["user_progress"] = StudyProgress.objects.filter(user=user, route=route).first()
        return context


class SaveNoteView(LoginRequiredMixin, View):
    def post(self, request):
        content_type_id = request.POST.get("content_type")
        object_id = request.POST.get("reaction")
        route_pk = request.POST.get("route")
        content = request.POST.get("content", "").strip()
        if content_type_id and object_id:
            ct = ContentType.objects.get_for_id(content_type_id)
            StudyNote.objects.update_or_create(
                user=request.user, content_type=ct, object_id=object_id,
                defaults={"content": content},
            )
        elif route_pk:
            StudyNote.objects.update_or_create(user=request.user, route_id=route_pk, defaults={"content": content})
        return redirect(request.META.get("HTTP_REFERER", "/"))
