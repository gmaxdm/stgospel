import json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


SUCCESS_CODE = [200, 204, 304, 404]


class Command(BaseCommand):
    args = ''
    help = 'Prepare cities.json file from cities.csv'
    leave_locale_alone = True

    def add_arguments(self, parser):
         parser.add_argument(
             '--code',
             dest="code",
             help="comma separated country codes to filter"
         )

    def handle(self, *args, **kwargs):
        with open(settings.CITIES_SRC_FILE) as f:
            lines = f.readlines()

        # if codes is [] all cities are saved
        codes = None
        if kwargs["code"]:
            codes = kwargs["code"].split(',')

        res = {}
        filtered = {}
        for ln in lines:
            arr = ln.split(';')
            city = arr[1][1:-1]
            tz = arr[2]
            code = arr[3]
            if codes is None or code in codes:
                try:
                    lt = filtered[city]
                except KeyError:
                    lt = filtered[city] = []
                lt.append(tz)

            key = "{}:{}:{}:{}".format(city, arr[4], arr[5], arr[6])
            if key in res:
                self.stdout.write("City '{}' is already in res".format(key))
                continue
            res[key] = {"tz": tz, "city": city, "countryName": arr[4], "regionName": arr[5], "cityName": arr[6]}

        with open(settings.CITIES_FILE, "w", encoding="utf8") as f:
            json.dump(res, f, ensure_ascii=False)

        if filtered:
            with open(settings.CITIES_FILTER_FILE, "w", encoding="utf8") as f:
                json.dump(filtered, f, ensure_ascii=False)

