from django.utils.deprecation import MiddlewareMixin
from django.db.models import F

from gospel.models import Counter
from gospel.json import is_json


class PageCounterMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not is_json(request):
            path = request.get_full_path()
            if len(path) > 200:
                path = path[:200]
            updated = Counter.objects.filter(path=path).update(count=F("count")+1)
            if updated == 0:
                Counter.objects.create(path=path, count=1)

