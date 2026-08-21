"""Shared view mixins (v4.0)."""

from django.contrib.contenttypes.models import ContentType

from ..forms import CommentForm
from ..services.comments import comments_for


class CommentContextMixin:
    """Inject comment context for any object detail view."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object
        context["comments"] = comments_for(obj).prefetch_related("replies")
        context["comment_form"] = CommentForm()
        context["comment_target"] = obj
        context["comment_content_type_id"] = ContentType.objects.get_for_model(obj).pk
        return context
