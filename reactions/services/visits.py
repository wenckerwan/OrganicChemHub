"""Visit counter helpers."""

from django.db.models import F
from django.utils import timezone

from ..models import VisitCounter


def _stats_for_counter(counter):
    today = timezone.localdate()
    return {
        "total": counter.total_count,
        "today": counter.today_count if counter.today_date == today else 0,
    }


def _increment_counter(key, label):
    today = timezone.localdate()
    counter, _ = VisitCounter.objects.get_or_create(
        key=key,
        defaults={"label": label, "today_date": today},
    )

    if counter.today_date != today:
        counter.today_date = today
        counter.today_count = 0
        counter.save(update_fields=["today_date", "today_count", "updated_at"])

    VisitCounter.objects.filter(pk=counter.pk).update(
        total_count=F("total_count") + 1,
        today_count=F("today_count") + 1,
    )
    counter.refresh_from_db(fields=["total_count", "today_count", "today_date", "updated_at"])
    return counter


def increment_site_visit():
    return _increment_counter(VisitCounter.SITE_KEY, "网站访问量")


def increment_object_visit(obj):
    counter = _increment_counter(VisitCounter.key_for_object(obj), str(obj))
    return _stats_for_counter(counter)


def get_site_visit_stats():
    today = timezone.localdate()
    counter, _ = VisitCounter.objects.get_or_create(
        key=VisitCounter.SITE_KEY,
        defaults={"label": "网站访问量", "today_date": today},
    )
    return _stats_for_counter(counter)
