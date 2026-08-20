"""Study topics and reaction comparison pages."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
from django.views.generic import DetailView, ListView

from ..models import GeneralReaction, NamedReaction, ReactionComparison, StudyProgress, StudyTopic, SyntheticRoute
from ..services.progress import topic_progress, topic_status_map
from ..services.visits import increment_object_visit


class StudyTopicListView(ListView):
    model = StudyTopic
    template_name = "reactions/study_topic_list.html"
    context_object_name = "topics"
    paginate_by = 12

    def get_queryset(self):
        queryset = StudyTopic.objects.filter(status=StudyTopic.Status.PUBLISHED)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(summary__icontains=query)
                | Q(learning_goals__icontains=query)
                | Q(exam_focus__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["comparison_count"] = ReactionComparison.objects.filter(status=ReactionComparison.Status.PUBLISHED).count()
        return context


class StudyTopicDetailView(DetailView):
    model = StudyTopic
    template_name = "reactions/study_topic_detail.html"
    context_object_name = "topic"
    queryset = StudyTopic.objects.filter(status=StudyTopic.Status.PUBLISHED).prefetch_related(
        "named_reactions", "general_reactions", "routes"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object
        user = self.request.user
        named = list(topic.named_reactions.filter(status=NamedReaction.Status.PUBLISHED))
        general = list(topic.general_reactions.filter(status=GeneralReaction.Status.PUBLISHED))
        routes = list(topic.routes.filter(status=SyntheticRoute.Status.PUBLISHED))

        named_ct = ContentType.objects.get_for_model(NamedReaction)
        general_ct = ContentType.objects.get_for_model(GeneralReaction)
        status_map = topic_status_map(user, topic)
        for reaction in named:
            reaction.user_status = status_map.get((named_ct.pk, reaction.pk), StudyProgress.Status.PENDING)
        for reaction in general:
            reaction.user_status = status_map.get((general_ct.pk, reaction.pk), StudyProgress.Status.PENDING)
        for route in routes:
            route.user_status = status_map.get(route.pk, StudyProgress.Status.PENDING)

        context["named_reactions"] = named
        context["general_reactions"] = general
        context["routes"] = routes
        context["named_ct_id"] = named_ct.pk
        context["general_ct_id"] = general_ct.pk
        context["topic_progress"] = topic_progress(user, topic)
        context["content_visit_stats"] = increment_object_visit(topic)
        return context


class ReactionComparisonListView(ListView):
    model = ReactionComparison
    template_name = "reactions/reaction_comparison_list.html"
    context_object_name = "comparisons"
    paginate_by = 12

    def get_queryset(self):
        queryset = ReactionComparison.objects.filter(status=ReactionComparison.Status.PUBLISHED)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(summary__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class ReactionComparisonDetailView(DetailView):
    model = ReactionComparison
    template_name = "reactions/reaction_comparison_detail.html"
    context_object_name = "comparison"
    queryset = ReactionComparison.objects.filter(status=ReactionComparison.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comparison = self.object
        context["reaction_a"] = comparison.reaction_a
        context["reaction_b"] = comparison.reaction_b
        if not context["reaction_a"] or not context["reaction_b"]:
            raise Http404
        if (
            getattr(context["reaction_a"], "status", None) != NamedReaction.Status.PUBLISHED
            and getattr(context["reaction_a"], "status", None) != GeneralReaction.Status.PUBLISHED
        ) or (
            getattr(context["reaction_b"], "status", None) != NamedReaction.Status.PUBLISHED
            and getattr(context["reaction_b"], "status", None) != GeneralReaction.Status.PUBLISHED
        ):
            raise Http404
        context["content_visit_stats"] = increment_object_visit(comparison)
        return context
