import os
import re
import ujson
import datetime
import requests
import html

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import DATE_FORMAT, TRAPEZA_ID, DATE_DELTA_DAY


SUCCESS_CODE = [200, 204, 304, 404]


URL = "https://script.pravoslavie.ru/calendar.php?advanced=1&feofan=1&date="


class Command(BaseCommand):
    args = ''
    help = 'Fetch trapeza from https://script.pravoslavie.ru/calendar.php'
    leave_locale_alone = True

    def fetch_trapeza(self, date, filename=None):
        resp = requests.get(URL + date)
        if resp.status_code not in SUCCESS_CODE:
            self.stdout.write("[{}]: {}".format(resp.status_code, resp.text))
            return
        if filename:
            with open(filename, "w") as f:
                f.write(resp.text)
        f = settings.RE_TRAPEZA.findall(resp.text)
        if len(f) > 1:
            print("WARN: found trapeza more then 1")
        elif not f:
            print("== ERROR ==: trapeza not found")
            return
        return f[0]

    def handle(self, *args, **kwargs):
        #dt = datetime.date(settings.CALENDAR_YEAR, 1, 1)
        stop_date = datetime.date(2026, 1, 15)
        dt = datetime.date(2025, 1, 1)
        #for day in range(settings.CALENDAR_PARAM_FROM, settings.CALENDAR_PARAM_TO + 1):
        #for day in (dt,):
        while dt < stop_date:
            sdt = dt.strftime(DATE_FORMAT)
        #for day in sorted(os.listdir(settings.CALENDAR_YEAR_DIR)):
        #    print("Inserting to {}".format(day))
        #    sdt, ext = os.path.splitext(day)
        #    dt = datetime.datetime.strptime(sdt, DATE_FORMAT)
            date = dt.strftime("%m%d")
            trapeza = self.fetch_trapeza(date,
                                         filename=os.path.join(settings.CALENDAR_SCRIPT, sdt))
            #trapeza = "Пища с растительным маслом."
            if 0 and trapeza:
                fname = "{}.json".format(sdt)
                with open(os.path.join(settings.CALENDAR_YEAR_DIR, fname)) as f:
                    data = ujson.loads(f.read())
                new_trapeza = html.unescape(trapeza).strip()
                if data["trapeza"] and data["trapeza"] != new_trapeza:
                    print("== Warning == New trapeza: {}, old: {}".format(new_trapeza, data["trapeza"]))
                data["trapeza"] = new_trapeza
                try:
                    data["trapeza_id"] = TRAPEZA_ID[data["trapeza"]]
                except KeyError:
                    data["trapeza_id"] = 0
                    print("== Error ==: Trapeza {} is not found".format(trapeza))
                with open(os.path.join(settings.CALENDAR_YEAR_DIR, fname), "w") as f:
                    f.write(ujson.dumps(data))
            dt += DATE_DELTA_DAY

