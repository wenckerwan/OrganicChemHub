"""Study progress aggregation helpers for the v2.6 review system.

All helpers are user-scoped and only aggregate published content.
They intentionally do not introduce any new models; they reuse ``StudyProgress``
(GenericForeignKey for reactions, route FK for synthetic routes).
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from ..models import GeneralReaction, NamedReaction, StudyProgress, StudyTopic, SyntheticRoute


def _published_items(topic):
    """Return (named, general, routes) lists restricted to published content."""
    named = list(topic.named_reactions.filter(status=NamedReaction.Status.PUBLISHED))
    general = list(topic.general_reactions.filter(status=GeneralReaction.Status.PUBLISHED))
    routes = list(topic.routes.filter(status=SyntheticRoute.Status.PUBLISHED))
    return named, general, routes


def _topic_progress_queryset(user, topic):
    """One query for all progress records of this user within a topic's published content."""
    named, general, routes = _published_items(topic)
    named_ct = ContentType.objects.get_for_model(NamedReaction)
    general_ct = ContentType.objects.get_for_model(GeneralReaction)
    return StudyProgress.objects.filter(user=user).filter(
        Q(content_type=named_ct, object_id__in=[r.pk for r in named])
        | Q(content_type=general_ct, object_id__in=[r.pk for r in general])
        | Q(route_id__in=[r.pk for r in routes])
    )


def topic_progress(user, topic):
    """Return ``{total, learned, review, pending, percent}`` for a topic.

    Returns ``None`` for anonymous users or topics without published content.
    """
    if not getattr(user, "is_authenticated", False):
        return None
    named, general, routes = _published_items(topic)
    total = len(named) + len(general) + len(routes)
    if total == 0:
        return None

    progress_qs = _topic_progress_queryset(user, topic)
    learned = progress_qs.filter(status=StudyProgress.Status.LEARNED).count()
    review = progress_qs.filter(status=StudyProgress.Status.REVIEW).count()
    return {
        "total": total,
        "learned": learned,
        "review": review,
        "pending": total - learned - review,
        "percent": round(learned / total * 100),
    }


def topic_status_map(user, topic):
    """Merged status mapping for template badges.

    Reaction keys are ``(content_type_id, object_id)`` tuples; route keys are
    plain route pks. Records that do not exist are simply absent from the map.
    """
    if not getattr(user, "is_authenticated", False):
        return {}
    mapping = {}
    for record in _topic_progress_queryset(user, topic):
        if record.route_id:
            mapping[record.route_id] = record.status
        else:
            mapping[(record.content_type_id, record.object_id)] = record.status
    return mapping


def user_topic_summary(user):
    """List of ``{topic, total, learned, percent}`` for published topics with content.

    Ordered by ``sort_order`` then name. Anonymous users get an empty list.
    """
    if not getattr(user, "is_authenticated", False):
        return []
    rows = []
    for topic in StudyTopic.objects.filter(status=StudyTopic.Status.PUBLISHED).order_by("sort_order", "name"):
        progress = topic_progress(user, topic)
        if progress is None:
            continue
        rows.append({"topic": topic, **progress})
    return rows


def review_queue(user):
    """All review-status progress records, most recently marked first."""
    if not getattr(user, "is_authenticated", False):
        return StudyProgress.objects.none()
    return StudyProgress.objects.filter(user=user, status=StudyProgress.Status.REVIEW).select_related(
        "route"
    ).order_by("-updated_at")


def recent_activity(user, limit=10):
    """Most recent progress records (any status), newest first."""
    if not getattr(user, "is_authenticated", False):
        return StudyProgress.objects.none()
    return StudyProgress.objects.filter(user=user).select_related("route").order_by("-updated_at")[:limit]
