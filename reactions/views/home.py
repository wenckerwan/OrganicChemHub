"""Home page and deploy guide views."""
from django.http import HttpResponse
from django.views.generic import TemplateView

from ..models import (
    Announcement,
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    SyntheticRoute,
    Tag,
)
from ..services.publication import publication_ready_count
from ..services.visits import get_site_visit_stats


class HomeView(TemplateView):
    template_name = "reactions/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_reactions"] = (
            NamedReaction.published.select_related("category").prefetch_related("tags").order_by("-updated_at")[:6]
        )
        context["reaction_types"] = NamedReactionCategory.objects.all()[:12]
        context["featured_general_reactions"] = (
            GeneralReaction.published.select_related("category").prefetch_related("tags").order_by("-updated_at")[:6]
        )
        context["general_reaction_categories"] = GeneralReactionCategory.objects.all()[:12]
        context["featured_routes"] = SyntheticRoute.published.order_by("-updated_at")[:4]
        context["tags"] = Tag.objects.all()[:12]
        context["functional_groups"] = FunctionalGroup.objects.all()[:12]
        named_published_count = NamedReaction.published.count()
        general_published_count = GeneralReaction.published.count()
        route_published_count = SyntheticRoute.published.count()
        ready_draft_count = publication_ready_count(NamedReaction) + publication_ready_count(GeneralReaction)
        context["frontend_content_status"] = {
            "named_published": named_published_count,
            "general_published": general_published_count,
            "routes_published": route_published_count,
            "publish_ready": ready_draft_count,
        }
        context["announcements"] = Announcement.objects.filter(is_active=True)[:5]
        context["popup_announcements"] = Announcement.objects.filter(
            is_active=True, is_pinned=True, importance=Announcement.Importance.HIGH
        )[:3]
        context["site_visit_stats"] = get_site_visit_stats()
        return context


class DeployGuideView(TemplateView):
    template_name = "reactions/deploy_guide.html"


def robots_txt_view(request):
    """Serve robots.txt pointing at the sitemap (v4.0)."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /profile/",
        "Disallow: /messages/",
        "Sitemap: {scheme}://{host}/sitemap.xml".format(
            scheme=request.scheme, host=request.get_host()
        ),
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
