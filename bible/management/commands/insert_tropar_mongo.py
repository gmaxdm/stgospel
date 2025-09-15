import os

from django.core.management.base import BaseCommand, CommandError
from gospel.models import OrthodoxCalendar
from stgospel.mongo import MongoDBClient as mongo


class Command(BaseCommand):
    args = ''
    help = 'insert troparion to Mongo for current year'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        for oc in OrthodoxCalendar.all():
            for title, prs in oc["prayers"].items():
                doc = {"title": title, "date": oc["date"], "text": prs}
                mongo.troparion_add(doc)

