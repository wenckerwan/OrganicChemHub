"""Content readiness report helpers (v3.0)."""
from ..models import GeneralReaction, NamedReaction

MODELS = [
    (NamedReaction, "NamedReaction"),
    (GeneralReaction, "GeneralReaction"),
]


def summary():
    """Return per-model readiness stats.

    Returns:
        {model_name: {total, ready, missing_fields, missing_images, placeholder_count}}
    """
    result = {}
    for model, name in MODELS:
        total = model.objects.count()
        ready = 0
        missing_fields = 0
        missing_images = 0
        placeholders = 0
        for obj in model.objects.all():
            missing = set(obj.get_publication_missing_fields())
            if not missing:
                ready += 1
                continue
            text_fields = {f for f in missing if f not in ("equation_img", "thumbnail_img", "mechanism_img")}
            img_fields = missing - text_fields
            if text_fields:
                missing_fields += 1
            if img_fields:
                missing_images += 1
            eq = getattr(obj, "equation_img", None)
            if eq and eq.name and "placeholder" in eq.name:
                placeholders += 1
        result[name] = {
            "total": total,
            "ready": ready,
            "missing_fields": missing_fields,
            "missing_images": missing_images,
            "placeholder_count": placeholders,
        }
    return result


def export_rows():
    """Yield per-object readiness rows as dicts."""
    for model, model_name in MODELS:
        for obj in model.objects.all():
            missing = set(obj.get_publication_missing_fields())
            text_fields = sorted(f for f in missing if f not in ("equation_img", "thumbnail_img", "mechanism_img"))
            img_fields = sorted(f for f in missing if f in ("equation_img", "thumbnail_img", "mechanism_img"))
            all_missing = text_fields + img_fields

            eq = getattr(obj, "equation_img", None)
            is_placeholder = bool(eq and eq.name and "placeholder" in eq.name)

            yield {
                "model": model_name,
                "name_zh": obj.name_zh,
                "slug": obj.slug,
                "status": obj.status,
                "missing": "、".join(all_missing) if all_missing else "",
                "placeholder": "是" if is_placeholder else "否",
                "ready": "是" if not missing else "否",
            }