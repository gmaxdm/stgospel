from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from bible.models import Line


class SearchView(TemplateView):
    template_name="search.html"

    def get(self, request, *args, **kwargs):
        try:
            s = request.GET["s"]
        except KeyError:
            return HttpResponseRedirect(reverse("main"))
        lines = (Line.objects.select_related("chapter", "chapter__book")
                             .filter(text__icontains=s))
        context = {
            "text": s,
            "lines": lines,
        }
        return render(request, self.template_name, context)

