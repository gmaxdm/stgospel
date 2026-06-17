import os
import ujson
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import DATE_FORMAT
#from gospel.utils import parse_reading


class Command(BaseCommand):
    args = ''
    help = 'Update and reconcile json calendar files'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
             '--date',
             dest="date",
             help="parse date in format YYYY-mm-dd"
        )
        parser.add_argument(
             '--title',
             dest="title",
             help="cnt lines of Saints lines will be title. Only applicable with --date"
        )

    def read(self, filename):
        with open(os.path.join(settings.CALENDAR_YEAR_DIR, filename)) as f:
            data = ujson.loads(f.read())
        return data

    def write(self, filename, data):
        with open(os.path.join(settings.CALENDAR_YEAR_DIR, filename), "w") as f:
            f.write(ujson.dumps(data))

    def handle(self, *args, **kwargs):
        trapeza = {}
        #for day in sorted(os.listdir(settings.CALENDAR_YEAR_DIR)):
        if 1:
            date = kwargs["date"]
            if date is None:
                date = "2023-04-15"
            datefile = f"{date}.json"
            dt = datetime.datetime.strptime(date, DATE_FORMAT)
            data = self.read(datefile)
            #data["rip"] = 1
            #data["easter"] = 1
            #data["carnival"] = 1
            data["twelve"] = 1

            #day2 = "2023-04-01.json"
            #data2 = self.read(day2)
            #data["trapeza"] = data2["trapeza"]
            #data["trapeza_id"] = data2["trapeza_id"]

            #_lines = []
            #for line in data["reading"]:
            #    m = RE_R.findall(line)
            #    print(m)
            #    _lines.append(line)
            #data["reading"] = _lines
            #print(_lines)
            self.write(datefile, data)

