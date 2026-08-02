"""Home page and deploy guide views."""
from django.utils import timezone
from django.views.generic import TemplateView

from ..models import (
    Announcement,
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    Reaction,
    ReactionType,
    SyntheticRoute,
    Tag,
)


class HomeView(TemplateView):
    template_name = "reactions/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uses_new_reactions = NamedReaction.published.exists()
        if uses_new_reactions:
            context["featured_reactions"] = (
                NamedReaction.published.select_related("category").prefetch_related("tags").order_by("-updated_at")[:6]
            )
            context["reaction_types"] = NamedReactionCategory.objects.all()[:12]
        else:
            context["featured_reactions"] = (
                Reaction.published.select_related("reaction_type").prefetch_related("tags").order_by("-updated_at")[:6]
            )
            context["reaction_types"] = ReactionType.objects.all()[:12]
        context["featured_general_reactions"] = (
            GeneralReaction.published.select_related("category").prefetch_related("tags").order_by("-updated_at")[:6]
        )
        context["general_reaction_categories"] = GeneralReactionCategory.objects.all()[:12]
        context["featured_routes"] = SyntheticRoute.published.order_by("-updated_at")[:4]
        context["tags"] = Tag.objects.all()[:12]
        context["functional_groups"] = FunctionalGroup.objects.all()[:12]
        now = timezone.now()
        context["announcements"] = Announcement.objects.filter(is_active=True)[:5]
        context["popup_announcements"] = Announcement.objects.filter(
            is_active=True, is_pinned=True, importance=Announcement.Importance.HIGH
        )[:3]
        return context


class DeployGuideView(TemplateView):
    template_name = "reactions/deploy_guide.html"