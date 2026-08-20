"""Placeholder SVG generation for reaction images (v3.0).

Generated SVGs are stored under ``reaction_images/placeholder/`` so the
dashboard can distinguish them from real uploaded images.
"""
import os

from django.conf import settings
from django.core.files.base import ContentFile


def equation_svg(title):
    """Return a neutral 1200×360 placeholder SVG for an equation image."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360">
  <rect width="1200" height="360" fill="#f8f9fa"/>
  <rect x="1" y="1" width="1198" height="358" fill="none" stroke="#adb5bd" stroke-width="2" stroke-dasharray="8 4"/>
  <text x="600" y="165" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#495057">{title}</text>
  <text x="600" y="215" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#868e96">方程式图片待补充</text>
</svg>"""


def thumbnail_svg(title):
    """Return a compact 400×300 placeholder SVG for a thumbnail."""
    first_char = title[0] if title else "?"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="#e9ecef"/>
  <rect x="3" y="3" width="394" height="294" fill="none" stroke="#ced4da" stroke-width="3"/>
  <text x="200" y="175" text-anchor="middle" font-family="Arial, sans-serif" font-size="64" fill="#6c757d">{first_char}</text>
</svg>"""


def placeholder_dir():
    """Absolute path to the placeholder subdirectory under MEDIA_ROOT."""
    path = os.path.join(settings.MEDIA_ROOT, "reaction_images", "placeholder")
    os.makedirs(path, exist_ok=True)
    return path


def _write_placeholder(instance, suffix, svg_text):
    filename = f"reaction_{instance.slug}_{suffix}.svg"
    full_path = os.path.join(placeholder_dir(), filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(svg_text)
    relative_path = os.path.join("reaction_images", "placeholder", filename)
    setattr(instance, suffix, relative_path)
    return relative_path


def placeholder_for(instance):
    """Generate equation and thumbnail placeholders for *instance* and bind both fields.

    Returns a list of field names that were bound.
    """
    bound = []
    if not instance.equation_img:
        _write_placeholder(instance, "equation_img", equation_svg(instance.name_zh))
        bound.append("equation_img")
    if not instance.thumbnail_img:
        _write_placeholder(instance, "thumbnail_img", thumbnail_svg(instance.name_zh))
        bound.append("thumbnail_img")
    if bound:
        instance.save(update_fields=bound + ["updated_at"])
    return bound