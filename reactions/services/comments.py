"""User comments on any content (v4.0)."""

from django.contrib.contenttypes.models import ContentType

from ..models import Comment


def comments_for(obj, include_hidden=False):
    """Return the comment queryset for an object, oldest first."""
    ct = ContentType.objects.get_for_model(obj)
    qs = Comment.objects.filter(content_type=ct, object_id=obj.pk).select_related("user", "parent__user")
    if not include_hidden:
        qs = qs.filter(is_hidden=False)
    return qs


def comment_count(obj):
    return comments_for(obj).count()


def create_comment(user, obj, body, parent_id=None):
    """Create a comment for an object, optionally as a reply to a top-level comment."""
    parent = None
    if parent_id:
        parent = Comment.objects.filter(pk=parent_id, is_hidden=False).first()
        if parent is None or parent.content_type_id != ContentType.objects.get_for_model(obj).pk:
            raise ValueError("无效的回复目标")
    return Comment.objects.create(user=user, content_object=obj, body=body.strip(), parent=parent)
