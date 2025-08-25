import os
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings


class Command(BaseCommand):
    help = 'Renders urls for JavaScript'

    def handle(self, *args, **kwargs):
        context = {
            "STATIC_URL": settings.STATIC_URL
        }
        js = render_to_string('urls.js', context)
        fname = os.path.join(settings.BASE_DIR, 'jsx', 'models', 'urls.jsx')
        with open(fname, "w") as f:
            f.write(js)

