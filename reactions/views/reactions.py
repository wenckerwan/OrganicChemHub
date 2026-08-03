"""Reaction list, detail, and common reactions views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, View

from ..models import (
    Favorite,
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    StudyNote,
    StudyProgress,
    Tag,
)


class ReactionListView(ListView):
    model = NamedReaction
    template_name = "reactions/reaction_list.html"
    context_object_name = "reactions"
    paginate_by = 12

    def get_queryset(self):
        queryset = NamedReaction.published.select_related("category").prefetch_related("tags", "functional_groups")
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
            queryset = queryset.filter(category__slug=type_slug)
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        if functional_group:
            queryset = queryset.filter(functional_groups__pk=functional_group)
        if exam == "1":
            queryset = queryset.filter(tags__slug__in=["exam-high-frequency", "postgraduate-exam-key"])

        queryset = queryset.distinct()
        if sort == "type":
            return queryset.order_by("category__sort_order", "category__id", "name_en", "name_zh")
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
        context["reaction_types"] = NamedReactionCategory.objects.all()
        context["tags"] = Tag.objects.all()
        context["functional_groups"] = FunctionalGroup.objects.all()
        context["reaction_index"] = self.object_list.order_by("name_en", "name_zh")[:120]
        context["recommended_reactions"] = NamedReaction.published.select_related("category").prefetch_related("tags")[:3]
        context["is_named_view"] = True
        context["supports_reaction_user_tools"] = False
        return context


class GeneralReactionListView(ListView):
    model = GeneralReaction
    template_name = "reactions/general_reaction_list.html"
    context_object_name = "reactions"
    paginate_by = 12

    def get_queryset(self):
        queryset = GeneralReaction.published.select_related("category").prefetch_related("tags", "functional_groups")
        query = self.request.GET.get("q", "").strip()
        type_slug = self.request.GET.get("type", "").strip()
        tag_slug = self.request.GET.get("tag", "").strip()
        functional_group = self.request.GET.get("functional_group", "").strip()
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
            queryset = queryset.filter(category__slug=type_slug)
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        if functional_group:
            queryset = queryset.filter(functional_groups__pk=functional_group)

        queryset = queryset.distinct()
        if sort == "type":
            return queryset.order_by("category__sort_order", "category__id", "name_zh", "name_en")
        if sort == "updated":
            return queryset.order_by("-updated_at", "name_zh", "name_en")
        return queryset.order_by("name_zh", "name_en")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_type"] = self.request.GET.get("type", "").strip()
        context["selected_tag"] = self.request.GET.get("tag", "").strip()
        context["selected_functional_group"] = self.request.GET.get("functional_group", "").strip()
        context["exam_filter"] = ""
        context["selected_sort"] = self.request.GET.get("sort", "name").strip() or "name"
        context["reaction_types"] = GeneralReactionCategory.objects.all()
        context["tags"] = Tag.objects.all()
        context["functional_groups"] = FunctionalGroup.objects.all()
        context["reaction_index"] = self.object_list.order_by("name_zh", "name_en")[:120]
        context["recommended_reactions"] = GeneralReaction.published.select_related("category").prefetch_related("tags")[:3]
        context["is_general_view"] = True
        context["supports_reaction_user_tools"] = False
        return context


class CommonReactionListView(View):
    """Legacy common-reaction URL kept only as a redirect to the new library."""

    def get(self, request, *args, **kwargs):
        return redirect("general_reaction_list")


class ReactionDetailView(DetailView):
    model = NamedReaction
    template_name = "reactions/reaction_detail.html"
    context_object_name = "reaction"

    queryset = NamedReaction.published.select_related("category").prefetch_related("tags", "functional_groups", "routes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rxn = self.object
        context["supports_reaction_user_tools"] = False
        if user.is_authenticated and context["supports_reaction_user_tools"]:
            context["is_favorited"] = Favorite.objects.filter(user=user, reaction=rxn).exists()
            context["user_note"] = StudyNote.objects.filter(user=user, reaction=rxn).first()
            context["user_progress"] = StudyProgress.objects.filter(user=user, reaction=rxn).first()
        return context


class GeneralReactionDetailView(DetailView):
    model = GeneralReaction
    template_name = "reactions/general_reaction_detail.html"
    context_object_name = "reaction"
    queryset = GeneralReaction.published.select_related("category").prefetch_related("tags", "functional_groups", "routes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_general_view"] = True
        context["supports_reaction_user_tools"] = False
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
