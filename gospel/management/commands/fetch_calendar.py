import os
import re
import datetime
import requests

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import DATE_FORMAT


SUCCESS_CODE = [200, 204]


def fix_2021_html(src):
    """ 2021 pages format fix
    """
    sep1 = "<hr>"
    head, body = re.split(sep1, src)
    head = head + "<div>" + sep1
    sep2 = "<div"
    saints, body = re.split(sep2, body, maxsplit=1)
    saints = saints + "</div>"
    body = sep2 + body
    return head + saints + body


class Command(BaseCommand):
    args = ''
    help = 'Fetch calendar from calendar.rop.ru'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        # set dt to correct file name: Ex, 2020-01-13
        delta = datetime.timedelta(days=1)
        #dt = datetime.date(2024, 3, 25)
        #for day in [85]:
        dt = datetime.date(settings.CALENDAR_YEAR, 1, 1)
        for day in range(settings.CALENDAR_PARAM_FROM, settings.CALENDAR_PARAM_TO + 1):
            url = "{}?{}={}".format(settings.CALENDAR_URL,
                                    settings.CALENDAR_PARAM,
                                    day)
            resp = requests.get(url)
            if resp.status_code not in SUCCESS_CODE:
                self.stdout.write("[{}]: {}".format(resp.status_code, resp.text))
                return
            #text = fix_2021_html(resp.text)
            text = resp.text
            filename = os.path.join(settings.CALENDAR_SRC, "{}.html".format(dt.strftime(DATE_FORMAT)))
            with open(filename, "w") as f:
                f.write(text)
            dt += delta

