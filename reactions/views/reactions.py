"""Reaction list, detail, and common reactions views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from ..models import (
    CommonReaction,
    Favorite,
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    PublishStatus,
    Reaction,
    ReactionType,
    StudyNote,
    StudyProgress,
    Tag,
)


def has_new_named_reactions():
    return NamedReaction.published.exists()


class ReactionListView(ListView):
    model = NamedReaction
    template_name = "reactions/reaction_list.html"
    context_object_name = "reactions"
    paginate_by = 12

    def get_queryset(self):
        self.uses_new_model = has_new_named_reactions()
        if self.uses_new_model:
            queryset = NamedReaction.published.select_related("category").prefetch_related("tags", "functional_groups")
            type_filter = "category__slug"
            type_order = ("category__sort_order", "category__id", "name_en", "name_zh")
        else:
            queryset = Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups")
            type_filter = "reaction_type__slug"
            type_order = ("reaction_type__sort_order", "reaction_type__id", "name_en", "name_zh")

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
            queryset = queryset.filter(**{type_filter: type_slug})
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        if functional_group:
            queryset = queryset.filter(functional_groups__pk=functional_group)
        if exam == "1":
            queryset = queryset.filter(tags__slug__in=["exam-high-frequency", "postgraduate-exam-key"])

        queryset = queryset.distinct()
        if sort == "type":
            return queryset.order_by(*type_order)
        if sort == "updated":
            return queryset.order_by("-updated_at", "name_en", "name_zh")
        return queryset.order_by("name_en", "name_zh")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uses_new_model = getattr(self, "uses_new_model", has_new_named_reactions())
        context["query"] = self.request.GET.get("q", "").strip()
        context["selected_type"] = self.request.GET.get("type", "").strip()
        context["selected_tag"] = self.request.GET.get("tag", "").strip()
        context["selected_functional_group"] = self.request.GET.get("functional_group", "").strip()
        context["exam_filter"] = self.request.GET.get("exam", "").strip()
        context["selected_sort"] = self.request.GET.get("sort", "name").strip() or "name"
        context["reaction_types"] = NamedReactionCategory.objects.all() if uses_new_model else ReactionType.objects.all()
        context["tags"] = Tag.objects.all()
        context["functional_groups"] = FunctionalGroup.objects.all()
        context["reaction_index"] = self.object_list.order_by("name_en", "name_zh")[:120]
        if uses_new_model:
            context["recommended_reactions"] = NamedReaction.published.select_related("category").prefetch_related("tags")[:3]
        else:
            context["recommended_reactions"] = Reaction.published.select_related("reaction_type").prefetch_related("tags")[:3]
        context["is_named_view"] = True
        context["supports_reaction_user_tools"] = not uses_new_model
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


class CommonReactionListView(ListView):
    """Dedicated view: common named reactions + non-person common reactions."""
    model = Reaction
    template_name = "reactions/common_reaction_list.html"
    context_object_name = "reactions"
    paginate_by = 20

    def get_queryset(self):
        return Reaction.published.filter(is_common=True).order_by("name_en", "name_zh")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["common_reactions"] = CommonReaction.objects.filter(status=PublishStatus.PUBLISHED).order_by("sort_order", "name_zh")
        context["is_common_view"] = True
        return context


class ReactionDetailView(DetailView):
    model = NamedReaction
    template_name = "reactions/reaction_detail.html"
    context_object_name = "reaction"

    def get_object(self, queryset=None):
        slug = self.kwargs.get("slug")
        try:
            self.uses_new_model = True
            return NamedReaction.published.select_related("category").prefetch_related("tags", "functional_groups", "routes").get(slug=slug)
        except NamedReaction.DoesNotExist:
            self.uses_new_model = False
            return get_object_or_404(
                Reaction.published.select_related("reaction_type").prefetch_related("tags", "functional_groups", "routes"),
                slug=slug,
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rxn = self.object
        uses_new_model = getattr(self, "uses_new_model", isinstance(rxn, NamedReaction))
        context["supports_reaction_user_tools"] = not uses_new_model
        if user.is_authenticated and not uses_new_model:
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