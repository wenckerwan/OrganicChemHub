"""Publication readiness helpers for reaction content."""

from django.utils import timezone

from ..models import PublishStatus


def publication_ready_queryset(model):
    """Return complete draft records that can be safely published."""
    ready_ids = [
        obj.pk
        for obj in model.objects.filter(status=PublishStatus.DRAFT).prefetch_related("images")
        if not obj.get_publication_missing_fields()
    ]
    return model.objects.filter(pk__in=ready_ids)


def publication_ready_count(model):
    return publication_ready_queryset(model).count()


def publish_ready_content(model):
    queryset = publication_ready_queryset(model)
    return queryset.update(status=PublishStatus.PUBLISHED, updated_at=timezone.now())
