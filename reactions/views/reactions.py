"""Reaction list, detail, and common reactions views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, View

from ..models import Favorite, FunctionalGroup, Reaction, ReactionType, StudyNote, StudyProgress, Tag


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
                Q(name_zh__icontains=query) | Q(name_en__icontains=query) | Q(aliases__icontains=query)
                | Q(condition__icontains=query) | Q(summary__icontains=query) | Q(exam_tips__icontains=query)
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
        context["recommended_reactions"] = Reaction.published.select_related("reaction_type").prefetch_related("tags")[:3]
        return context


class CommonReactionListView(ReactionListView):
    """Dedicated view for common reactions (is_common=True)."""

    def get_queryset(self):
        queryset = Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups")
        return queryset.filter(is_common=True).distinct().order_by("name_en", "name_zh")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_common_view"] = True
        context["exam_filter"] = ""
        return context


class ReactionDetailView(DetailView):
    model = Reaction
    template_name = "reactions/reaction_detail.html"
    context_object_name = "reaction"
    queryset = Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups", "routes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rxn = self.object
        if user.is_authenticated:
            context["is_favorited"] = Favorite.objects.filter(user=user, reaction=rxn).exists()
            context["user_note"] = StudyNote.objects.filter(user=user, reaction=rxn).first()
            context["user_progress"] = StudyProgress.objects.filter(user=user, reaction=rxn).first()
        return context


class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request):
        reaction_pk = request.POST.get("reaction")
        route_pk = request.POST.get("route")
        user = request.user
        if reaction_pk:
            fav, created = Favorite.objects.get_or_create(user=user, reaction_id=reaction_pk)
            if not created:
                fav.delete()
        elif route_pk:
            fav, created = Favorite.objects.get_or_create(user=user, route_id=route_pk)
            if not created:
                fav.delete()
        return redirect(request.META.get("HTTP_REFERER", "/"))


class UpdateProgressView(LoginRequiredMixin, View):
    def post(self, request):
        reaction_pk = request.POST.get("reaction")
        route_pk = request.POST.get("route")
        status = request.POST.get("status", StudyProgress.Status.PENDING)
        user = request.user
        if reaction_pk:
            StudyProgress.objects.update_or_create(user=user, reaction_id=reaction_pk, defaults={"status": status})
        elif route_pk:
            StudyProgress.objects.update_or_create(user=user, route_id=route_pk, defaults={"status": status})
        return redirect(request.META.get("HTTP_REFERER", "/"))
