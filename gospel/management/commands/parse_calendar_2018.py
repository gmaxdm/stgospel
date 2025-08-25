import os
import datetime
import ujson
import re
from html.parser import HTMLParser

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import DATE_FORMAT


SEP_BEGIN = "udiz_koren.txt begin"
SEP_END = "udiz_koren.txt end"
INCLUDE_TAGS = ["sup", "b", "strong", "small"]
ENDLINE_TAGS = ["br", "p", "center"]

LINE_ENDS = (".", "!")


class Parser(HTMLParser):

    div_tag = "div"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inside = False
        self.divs = []
        self.line = []
        self.lines = []

    def add(self, line):
        if self.inside:
            self.line.append(line)

    def flush_line(self):
        if self.inside and self.line:
            #print(self.line)
            self.lines.append("".join(self.line))
            self.line = []

    def handle_data(self, data):
        if data:
            self.add(data)

    def handle_starttag(self, tag, attrs):
        if tag == self.div_tag:
            self.inside = True
            for attr in attrs:
                if attr[0] == "class" and attr[1] == "spu-bu-snoski":
                    self.lines = self.divs.pop()
        elif tag in INCLUDE_TAGS:
            self.add("<{}>".format(tag))
        elif tag in ENDLINE_TAGS:
            self.flush_line()

    def handle_endtag(self, tag):
        if tag == self.div_tag:
            self.flush_line()
            self.divs.append(self.lines)
            self.lines = []
            self.inside = False
        elif tag in INCLUDE_TAGS:
            self.add("</{}>".format(tag))
        elif tag in ENDLINE_TAGS:
            self.flush_line()


class Calendar:

    def __init__(self):
        self.title = []
        self.saints = []
        self.reading = []
        self.prayers = []
        self.preaching = []

    @staticmethod
    def __replace_sup(lines):
        sups = {}
        s = 0
        ids = []
        for i, line in enumerate(lines):
            if "sup" in line:
                s += line.count("<sup>")
                continue
            for n in range(s):
                if line.startswith(str(n+1)):
                    ids.append(i)
                    sups[n] = line[3:]
                    break
        if s == 0:
            return
        _new = []
        s = 0
        for i, line in enumerate(lines):
            if "sup" in line:
                cnt = line.count("<sup>")
                _line = line
                for n in range(cnt):
                    _line = re.sub("<sup>\s*{}\s*<\/sup>".format(n+1),
                                   ' (<small class="text-muted">{}</small>)'
                                   .format(sups[n]), _line)
                _new.append(_line)
                s += cnt
                continue
            if i in ids:
                continue
            _new.append(line)
        return _new

    def set_title(self, lines):
        self.title = lines

    def set_saints(self, lines):
        sup = False
        self.saints = []
        for line in lines:
            if "sup" in line:
                sup = True
            if line.startswith("."):
                self.saints[-1] = self.saints[-1] + line
            else:
                self.saints.append(line)
        if sup:
            # replace sup in saints:
            self.saints = self.__replace_sup(self.saints)

    def set_reading(self, lines):
        sup = False
        self.reading = []
        for line in lines:
            if "sup" in line:
                sup = True
            if line.startswith("."):
                self.reading[-1] = self.reading[-1] + line
            else:
                self.reading.append(line)
        if sup:
            # replace sup in reading:
            self.reading = self.__replace_sup(self.reading)

    def set_prayers(self, lines):
        self.prayers = {}
        pr = None
        for line in lines:
            if line.endswith(":"):
                if pr is not None and not pr:
                    print("[ERROR]: pray without pray: {}".format(lines))
                pr = self.prayers[line] = []
            elif line.endswith(LINE_ENDS):
                if pr is None:
                    print("[ERROR]: pray without name: {}".format(lines))
                    continue
                pr.append(line)

    def set_preaching(self, lines):
        self.preaching = lines

    def __str__(self):
        return ("TITLE: {}\n"
                "SAINTS: {}\n"
                "READING: {}\n"
                "PRAYERS: {}\n"
                "PREACHING: {}\n".format("\n".join(self.title),
                                         "\n".join(self.saints),
                                         "\n".join(self.reading),
                                         "\n".join(self.prayers),
                                         "\n".join(self.preaching)))
    def to_json(self):
        return {
            "title": self.title,
            "saints": self.saints,
            "reading": self.reading,
            "prayers": self.prayers,
            "preaching": self.preaching,
        }


class Command(BaseCommand):
    args = ''
    help = 'Parse calendar from calendar.rop.ru'
    leave_locale_alone = True


    def add_arguments(self, parser):
        parser.add_argument(
             '--date',
             dest="date",
             help="parse date in format %Y-%m-%d (today if None)"
        )

    def __parse_date(self, date):
        filename = "{}.html".format(date.strftime(DATE_FORMAT))
        name, _ = os.path.splitext(filename)
        with open(os.path.join(settings.CALENDAR_SRC, filename)) as f:
            data = f.read()
        inside = False
        inner = []
        for ln in data.split("\n"):
            #line = ln.strip()
            line = ln.replace("¶", "").replace("\ufeff", "")
            if SEP_END in line:
                if inside:
                    break
            if SEP_BEGIN in line:
                inside = True
                continue
            if inside:
                inner.append(line)
        inner_part = "".join(inner)
        #self.stdout.write(inner_part)
        parser = Parser()
        parser.feed(inner_part)
        calendar = Calendar()
        calendar.set_title(parser.divs[2])
        calendar.set_saints(parser.divs[3])
        calendar.set_reading(parser.divs[4])
        calendar.set_prayers(parser.divs[6])
        calendar.set_preaching(parser.divs[8])
        #self.stdout.write(str(calendar))
        #for div in parser.divs:
        #    self.stdout.write("DIV: {}".format("\n".join(div)))
        with open(os.path.join(settings.CALENDAR_YEAR_DIR,
                               "{}.json".format(name)), "w") as f:
            f.write(ujson.dumps(calendar.to_json()))

    def handle(self, *args, **kwargs):
        today = datetime.datetime.now().date()
        date = kwargs["date"]
        if date is None:
            delta = datetime.timedelta(days=1)
            start = datetime.date(settings.CALENDAR_YEAR, 1, 1)
            from_id = (today - start).days + 1
            dt = today
            for day in range(from_id, settings.CALENDAR_TO):
                self.__parse_date(dt)
                dt += delta
        else:
            try:
                dt = datetime.datetime.strptime(date, DATE_FORMAT).date()
            except (TypeError, ValueError):
                dt = today
            self.__parse_date(dt)

