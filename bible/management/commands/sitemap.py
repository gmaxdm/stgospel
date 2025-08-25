import os
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

from stgospel.mongo import MongoDBClient as mongo

from bible.models import Book, Pray
from forum.models import Forum, Topic
from gospel.models import DATE_FORMAT, DATE_DELTA_DAY


SITEMAP_FILE = os.path.join(settings.BASE_DIR, 'root', 'sitemap.xml')


class Command(BaseCommand):
    args = ''
    help = 'Render sitemap.xml'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        today = datetime.datetime.now().date().strftime(DATE_FORMAT)
        urls = []
        for book in Book.objects.all():
            urls.append(reverse("book", kwargs={"slug": book.slug}))
            for num in range(1, book.chapters+1):
                urls.append(reverse("chapter", kwargs={"slug": book.slug,
                                                       "num": num}))

        for pray in Pray.objects.all():
            urls.append(reverse("pray", kwargs={"slug": pray.slug}))

        for pray in mongo.get_troparions(""):
            urls.append(reverse("tropar") + "?id=" + str(pray["_id"]))

        for forum in Forum.objects.filter(visible=True):
            urls.append(reverse("forum-view", args=(forum.slug,)))

        for topic in Topic.objects.select_related("forum").filter(forum__visible=True):
            urls.append(reverse("forum-topic",
                                args=(topic.forum.slug, topic.slug)))

        dt = datetime.datetime(settings.CALENDAR_YEAR, 1, settings.CALENDAR_PARAM_FROM).date()
        for d in range(settings.CALENDAR_PARAM_FROM, settings.CALENDAR_PARAM_TO):
            urls.append(reverse("calendar", kwargs={
                                                "year": dt.year,
                                                "month": dt.month,
                                                "day": dt.day,
                                            }))
            dt += DATE_DELTA_DAY

        sitemap = render_to_string("sitemap.xml", {
            "urls": urls,
            "date": today,
            "kathisma": list(range(1, 21)),
        })
        with open(SITEMAP_FILE, "w") as f:
            f.write(sitemap)

