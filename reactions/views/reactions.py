"""Reaction list, detail, and common reactions views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
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
from ..services.visits import increment_object_visit


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
        context["library_title"] = "人名反应库"
        context["library_eyebrow"] = "Named Reaction Library"
        context["library_description"] = "收录以发现者或经典命名方式流传的人名反应，适合按名称、官能团、机理考点和合成用途快速查询。"
        context["library_sidebar_label"] = "人名反应目录"
        context["library_all_label"] = "全部已发布人名反应"
        context["library_empty_label"] = "没有找到匹配的已发布人名反应。"
        context["library_index_empty_label"] = "暂无已发布人名反应"
        context["library_search_placeholder"] = "搜索人名反应、试剂、考点"
        context["library_theme"] = "named"
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
        context["library_title"] = "常见有机反应库"
        context["library_eyebrow"] = "General Reaction Library"
        context["library_description"] = "整理加成、取代、消除、氧化还原等常见有机反应类型，适合按反应类别、官能团和考研场景快速复习。"
        context["library_sidebar_label"] = "常见反应目录"
        context["library_all_label"] = "全部已发布常见反应"
        context["library_empty_label"] = "没有找到匹配的已发布常见反应。"
        context["library_index_empty_label"] = "暂无已发布常见反应"
        context["library_search_placeholder"] = "搜索常见反应、官能团、考点"
        context["library_theme"] = "general"
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

    queryset = NamedReaction.published.select_related("category").prefetch_related("tags", "functional_groups", "routes", "images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rxn = self.object
        context["content_visit_stats"] = increment_object_visit(rxn)
        context["supports_reaction_user_tools"] = True
        if user.is_authenticated:
            ct = ContentType.objects.get_for_model(rxn)
            context["is_favorited"] = Favorite.objects.filter(user=user, content_type=ct, object_id=rxn.pk).exists()
            context["user_note"] = StudyNote.objects.filter(user=user, content_type=ct, object_id=rxn.pk).first()
            context["user_progress"] = StudyProgress.objects.filter(user=user, content_type=ct, object_id=rxn.pk).first()
            context["content_type_id"] = ct.pk
        return context


class GeneralReactionDetailView(DetailView):
    model = GeneralReaction
    template_name = "reactions/general_reaction_detail.html"
    context_object_name = "reaction"
    queryset = GeneralReaction.published.select_related("category").prefetch_related("tags", "functional_groups", "routes", "images")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rxn = self.object
        context["content_visit_stats"] = increment_object_visit(rxn)
        context["is_general_view"] = True
        context["supports_reaction_user_tools"] = True
        if user.is_authenticated:
            ct = ContentType.objects.get_for_model(rxn)
            context["is_favorited"] = Favorite.objects.filter(user=user, content_type=ct, object_id=rxn.pk).exists()
            context["user_note"] = StudyNote.objects.filter(user=user, content_type=ct, object_id=rxn.pk).first()
            context["user_progress"] = StudyProgress.objects.filter(user=user, content_type=ct, object_id=rxn.pk).first()
            context["content_type_id"] = ct.pk
        return context


class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request):
        content_type_id = request.POST.get("content_type")
        object_id = request.POST.get("reaction")
        route_pk = request.POST.get("route")
        user = request.user
        if content_type_id and object_id:
            ct = ContentType.objects.get_for_id(content_type_id)
            fav, created = Favorite.objects.get_or_create(
                user=user, content_type=ct, object_id=object_id,
            )
            if not created:
                fav.delete()
        elif route_pk:
            fav, created = Favorite.objects.get_or_create(user=user, route_id=route_pk)
            if not created:
                fav.delete()
        return redirect(request.META.get("HTTP_REFERER", "/"))


class UpdateProgressView(LoginRequiredMixin, View):
    def post(self, request):
        content_type_id = request.POST.get("content_type")
        object_id = request.POST.get("reaction")
        route_pk = request.POST.get("route")
        status = request.POST.get("status", StudyProgress.Status.PENDING)
        user = request.user
        if content_type_id and object_id:
            ct = ContentType.objects.get_for_id(content_type_id)
            StudyProgress.objects.update_or_create(
                user=user, content_type=ct, object_id=object_id,
                defaults={"status": status},
            )
        elif route_pk:
            StudyProgress.objects.update_or_create(user=user, route_id=route_pk, defaults={"status": status})
        return redirect(request.META.get("HTTP_REFERER", "/"))
