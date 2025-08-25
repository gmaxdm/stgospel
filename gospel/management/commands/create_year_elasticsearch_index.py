import json
from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl import Index

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import OrthodoxCalendar


def correct_prayers_dict(data):
    new_prayers = []
    for k, v in data.get("prayers", {}).items():
        new_prayers.append({
            "title": k,
            "text": v
        })
    data["prayers"] = new_prayers
    return data


def genIndexCalendarSource(index, data):
    for d in data:
        yield {
            "_index": index,
            "_source": correct_prayers_dict(d)
        }


def genIndexPrayerSource(index, data):
    for d in data:
        _d = correct_prayers_dict(d)
        for p in _d["prayers"]:
            yield {
                "_index": index,
                "_source": p
            }


class Command(BaseCommand):
    args = ''
    help = 'Creates ElasticSearch index for current OrthodoxCalendar'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
             '--index',
             dest="index",
             help="index type: calendar or prayer"
        )

    def create_index(self, client, name):
        # creating index
        self.stdout.write("creating index {}:".format(name))
        index = Index(name, using=client)
        res = index.create()
        self.stdout.write(json.dumps(res, indent=4))

    def handle(self, *args, **kwargs):
        client = Elasticsearch(HOST="http://localhost", PORT=9200)

        try:
            index_type = kwargs["index"]
            if index_type not in ("calendar", "prayer"):
                raise KeyError
        except KeyError:
            index_type = "calendar"
        index_name = "{}-{}".format(index_type, settings.CALENDAR_YEAR)
        self.create_index(client, index_name)

        if index_type == "calendar":
            genSource = genIndexCalendarSource
        elif index_type == "prayer":
            genSource = genIndexPrayerSource

        self.stdout.write("inserting calendar data:")
        helpers.bulk(client, genSource(index_name,
                                       OrthodoxCalendar.all()))
        self.stdout.write("done")

