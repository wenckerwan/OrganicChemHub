"""Frontend visit counting middleware."""

from .services.visits import increment_site_visit


class SiteVisitCounterMiddleware:
    SKIPPED_PREFIXES = ("/admin/", "/static/", "/media/", "/favicon.ico")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        should_count = self.should_count(request)
        if should_count:
            increment_site_visit()
        response = self.get_response(request)
        return response

    def should_count(self, request):
        if request.method != "GET":
            return False
        return not request.path.startswith(self.SKIPPED_PREFIXES)
