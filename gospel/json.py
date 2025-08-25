import logging
import datetime

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger(__name__)


def is_json(request):
    _accept = request.META.get("HTTP_ACCEPT")
    return _accept and "json" in _accept


def json_require_response():
    resp = HttpResponse("use json request")
    resp.status_code = 420
    return resp


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            if isinstance(obj, datetime.date):
                return obj.strftime(DATE_FORMAT)
            if hasattr(obj, "__iter__"):
                lt = []
                for it in obj:
                    try:
                        lt.append(it.to_json())
                    except AttributeError:
                        lt.append(it)
                return lt
            if hasattr(obj, "to_json"):
                return obj.to_json()
            raise

class JsonView(View):

    def get(self, request, *args, **kwargs):
        if is_json(request):
            return JsonResponse(self.get_data(request, *args, **kwargs),
                                encoder=LazyEncoder)
        return json_require_response()

    def get_data(request, *args, **kwargs):
        return {}


class JsonFileView(View):

    def get(self, request, *args, **kwargs):
        if is_json(request):
            resp = HttpResponse(self.get_filedata(request, *args, **kwargs),
                                content_type="application/json")
            return resp
        return json_require_response()

    def get_filedata(request, *args, **kwargs):
        return ""


class JsonListView(ListView):
    queryset = None

    def get(self, request, *args, **kwargs):
        if is_json(request):
            res = {}
            queryset = self.get_queryset()
            if queryset is not None:
                res = {it.id: it for it in queryset}
            return JsonResponse(res, encoder=LazyEncoder)
        return super().get(request, *args, **kwargs)


class JsonContextView(TemplateView):
    # some default template for Json requests
    template_name = "about.html"
    json_only = False

    def get(self, request, *args, **kwargs):
        if is_json(request):
            context = self.get_context_data(**kwargs)
            del context["view"]
            return JsonResponse(context, encoder=LazyEncoder)
        elif self.json_only:
            return json_require_response()
        return super().get(request, *args, **kwargs)

