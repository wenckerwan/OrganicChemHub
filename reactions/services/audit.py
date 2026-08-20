"""Audit log and content batch recording helpers (v2.8)."""
import json

from ..models import ContentBatch, OpLog


def log_operation(user, action, model_name, object_repr, detail="", ip=None):
    """Create an OpLog entry for an admin operation."""
    OpLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_repr=object_repr,
        detail=detail,
        ip=ip,
    )


def record_batch(kind, operator, summary, objects, detail=""):
    """Create a ContentBatch record.

    ``objects`` is a list of object names used only for counting;
    ``detail`` is stored as JSON text truncated to 2000 chars.
    """
    payload = json.dumps(detail, ensure_ascii=False) if not isinstance(detail, str) else detail
    return ContentBatch.objects.create(
        kind=kind,
        operator=operator if operator and operator.is_authenticated else None,
        summary=summary,
        detail=payload[:2000],
        object_count=len(objects),
    )
