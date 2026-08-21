"""Sitemap definitions for public content (v4.0)."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import (
    GeneralReaction,
    LearningResource,
    NamedReaction,
    ReactionComparison,
    StudyTopic,
    SyntheticRoute,
)


class StaticViewSitemap(Sitemap):
    """Static top-level pages."""

    priority = 0.9
    changefreq = "daily"

    def items(self):
        return ["home", "reaction_list", "general_reaction_list", "route_list", "study_topic_list", "reaction_comparison_list", "learning_resource_list"]

    def location(self, item):
        return reverse(item)


class NamedReactionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return NamedReaction.published.all()

    def lastmod(self, obj):
        return obj.updated_at


class GeneralReactionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return GeneralReaction.published.all()

    def lastmod(self, obj):
        return obj.updated_at


class SyntheticRouteSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return SyntheticRoute.published.all()

    def lastmod(self, obj):
        return obj.updated_at


class StudyTopicSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return StudyTopic.objects.filter(status=StudyTopic.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at


class ReactionComparisonSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ReactionComparison.objects.filter(status=ReactionComparison.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at


class LearningResourceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return LearningResource.objects.all()


sitemaps = {
    "static": StaticViewSitemap,
    "named_reactions": NamedReactionSitemap,
    "general_reactions": GeneralReactionSitemap,
    "routes": SyntheticRouteSitemap,
    "topics": StudyTopicSitemap,
    "comparisons": ReactionComparisonSitemap,
    "resources": LearningResourceSitemap,
}
