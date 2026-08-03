"""Publication readiness helpers for reaction content."""

from django.utils import timezone

from ..models import PublishStatus


def publication_ready_queryset(model):
    """Return complete draft records that can be safely published."""
    queryset = model.objects.filter(status=PublishStatus.DRAFT)
    for field in model.REQUIRED_FIELDS:
        queryset = queryset.exclude(**{field: ""}).exclude(**{f"{field}__isnull": True})
    return queryset


def publication_ready_count(model):
    return publication_ready_queryset(model).count()


def publish_ready_content(model):
    queryset = publication_ready_queryset(model)
    return queryset.update(status=PublishStatus.PUBLISHED, updated_at=timezone.now())
