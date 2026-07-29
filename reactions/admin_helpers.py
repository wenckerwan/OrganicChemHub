"""Shared helpers for admin configuration."""
from django.utils.html import format_html


def image_preview(url, max_w=420, max_h=220):
    """Render an image preview HTML snippet, or a placeholder if url is empty."""
    if not url:
        return "暂无图片"
    return format_html(
        '<img src="{}" style="max-width:{}px;max-height:{}px;background:#fff;'
        'border:1px solid #d8dee8;border-radius:8px;padding:8px;">',
        url, max_w, max_h,
    )


def thumbnail_img(url):
    """Render a small square thumbnail, or a dash if empty."""
    if not url:
        return "—"
    return format_html(
        '<img src="{}" style="width:60px;height:60px;object-fit:contain;'
        'background:#fff;border:1px solid #ddd;border-radius:4px;">', url,
    )
