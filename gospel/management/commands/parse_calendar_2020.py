import os
import datetime
import ujson
import re
import html
from html.parser import HTMLParser

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import DATE_FORMAT, TRAPEZA_ID
from gospel.utils import (clean_tags, replace_readings, split_readings,
                          split_by_index, is_similar)
from bible.ref_parser.ref_parser import RefParser


SEP_BEGIN = "udiz_koren.txt begin"
SEP_END = "udiz_koren.txt end"
INCLUDE_TAGS = ["b", "strong", "small"]
ENDLINE_TAGS = ["br", "p", "center"]

LINE_ENDS = (".", "!")


rePrTitle = re.compile(r"[\w\s\.,\(\)]+[^:]$")


with open(settings.HOLYDAY_DATA) as f:
    HOLYDAY = ujson.loads(f.read())


with open(settings.PRAYER_GENERIC_DATA) as f:
    PRAYER_GENERIC = ujson.loads(f.read())


class SupLine(str):
    index = []
    sups = []


class Div:
    """Contains Lines:
    - Div
    - SupLine
    """

    def __init__(self):
        self.line = []
        self.lines = []
        self.index = []
        self.sups = []

    def __iter__(self):
        return iter(self.lines)

    def add(self, data):
        if data:
            self.line.append(data)

    def add_line(self, line):
        if line:
            self.lines.append(line)

    def flush_line(self):
        if self.line:
            sp = SupLine("".join(self.line))
            sp.index = self.index
            sp.sups = self.sups
            self.add_line(sp)
            self.line = []
            self.index = []
            self.sups = []

    def __str__(self):
        # SupLine is broken here
        return "\n".join(map(str, self.lines))


class Parser(HTMLParser):
    """ This parser is oriented to parse the following pattern:
        div0: date
        div1: saints, reading
        div2: line (to exclude)
        div3: prayers (with inner divs as prayer titles)
        div4: line (to exclude)
        div5: preaching
    """
    div_tag = "div"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sups = None  # inside the spu-bu-snoski div
        self.sups_cnt = 0
        self.catch_sup = False
        self.inside_sup = False
        self.divs = []
        self.cur_div = None
        self.content = []

    def handle_data(self, data):
        if not data:
            return
        if self.catch_sup:
            if self.sups is not None:
                self.sups.append(data.strip())
        elif self.cur_div:
            if not self.inside_sup:
                self.cur_div.add(data)

    def handle_starttag(self, tag, attrs):
        self.catch_sup = False
        if tag == self.div_tag:
            if self.cur_div:
                # handle not closing prev tags:
                self.cur_div.flush_line()
            for attr in attrs:
                if attr[0] == "class" and attr[1] == "spu-bu-snoski":
                    self.sups = []
            # ignoring contens[9] sups
            if self.sups is None:
                self.cur_div = Div()
                self.divs.append(self.cur_div)
        elif tag == "sup":
            if self.sups is None:
                self.inside_sup = True
                self.sups_cnt += 1
                idx = sum(map(len, self.cur_div.line))
                self.cur_div.index.append(idx)
                self.cur_div.sups.append(self.sups_cnt)
        elif self.cur_div:
            if tag in INCLUDE_TAGS:
                self.cur_div.add("<{}>".format(tag))
            elif tag in ENDLINE_TAGS:
                self.cur_div.flush_line()

    def handle_endtag(self, tag):
        if tag == "sup" or tag == "a":
            if self.sups is not None:
                self.catch_sup = True
            self.inside_sup = False
        elif self.cur_div:
            if tag == self.div_tag:
                self.cur_div.flush_line()
                _div = self.divs.pop()
                try:
                    self.cur_div = self.divs[-1]
                    self.cur_div.add_line(_div)
                except IndexError:
                    self.cur_div = None
                    self.content.append(_div)
            elif tag in INCLUDE_TAGS:
                self.cur_div.add("</{}>".format(tag))
            elif tag in ENDLINE_TAGS:
                self.cur_div.flush_line()
        else:
            if tag == self.div_tag and self.sups is None:
                print("== ERROR ==: closing DIV without start tag!")

    def extract_reading(self):
        lines = []
        reading = []
        for line in self.content[2].lines:
            line = line.replace("_", " ")
            rp = RefParser(line)
            if rp.refs:
                _line = replace_readings(rp.refs, line)
                _refs = split_readings(_line)
                if _line.count("</a>") != sum([_r.count("</a>") for _r in _refs]):
                    print("== ERROR == reading refs not match links count")
                reading.append(_refs)
            else:
                lines.append(line)
        self.content[2].lines = lines
        return reading

    def replace_sups(self):
        if self.sups:

            def __replace_sups(div):
                _changed = False
                _div = Div()
                for line in div.lines:
                    _ch = False
                    if isinstance(line, Div):
                        _d, _ch = __replace_sups(line)
                        _div.add_line(_d)
                    else:
                        idx = line.index
                        if idx:
                            _arr = []
                            for i, st in enumerate(split_by_index(line, idx)):
                                _arr.append(st)
                                try:
                                    _arr.append(' (<small class="text-muted">{}</small>)'
                                                .format(self.sups[line.sups[i]-1]))
                                    _ch = True
                                except IndexError:
                                    pass
                            _line = "".join(_arr)
                        else:
                            _line = line
                        _div.add_line(_line)
                    _changed = _changed or _ch
                return _div, _changed

            for i, div in enumerate(self.content[1:6]):
                _div, changed = __replace_sups(div)
                if changed:
                    self.content[i+1] = _div


class Calendar:

    def __init__(self, date):
        self.title = []
        self.saints = []
        self.reading = []
        self.prayers = []
        self.preaching = []
        self.feofan = None
        self.str_date = date
        self.date = datetime.datetime.strptime(date, DATE_FORMAT).date()
        with open(os.path.join(settings.CALENDAR_SCRIPT, date)) as f:
            text = f.read()
        f = settings.RE_TRAPEZA.findall(text)
        self.trapeza = html.unescape(f[0]).strip()
        try:
            self.trapeza_id = TRAPEZA_ID[self.trapeza]
        except KeyError:
            self.trapeza_id = 0
            print("== Error ==: Trapeza {} is not found".format(self.trapeza))
        f = settings.RE_FEOFAN.findall(text)
        try:
            _feofan = clean_tags(f[0]).replace("\\", "").strip()
            rp = RefParser(_feofan)
            self.feofan = replace_readings(rp.refs, _feofan)
        except IndexError:
            print("can't find Feofan")

    def set_title(self, div, lines=0):
        if lines == 0 and self.date.isoweekday() == 7:
            lines = 1
        if lines:
            self.title = div.lines[:lines]
            div.lines = div.lines[lines:]

    def set_saints(self, lines):
        self.saints = lines

    def set_reading(self, lines):
        self.reading = lines

    def set_prayers(self, div):
        self.prayers = {}
        pr = None
        holyday_parse = False
        for line in div.lines:
            if isinstance(line, Div):
                _line = str(line)
                if rePrTitle.match(_line):
                    print("skipping Title line: {}".format(_line))
                    continue
                if pr is not None and not pr:
                    print("[ERROR]: pray without pray: {}".format(_line))
                if "арь и кондак воскресн" in _line:
                    holyday_parse = True
                    reH = re.compile("\d+")
                    d = reH.findall(_line)[0]
                    pr = self.prayers["Тропарь воскресный {}-го гласа:".format(d)] = []
                    pr.append(HOLYDAY[d]["troparion"])
                    pr = self.prayers["Кондак воскресный {}-го гласа:".format(d)] = []
                    pr.append(HOLYDAY[d]["konduk"])
                    pr = None
                elif "Тропарь воскресный" in _line:
                    holyday_parse = True
                    reH = re.compile("\d+")
                    d = reH.findall(_line)[0]
                    pr = self.prayers["Тропарь воскресный {}-го гласа:".format(d)] = []
                    pr.append(HOLYDAY[d]["troparion"])
                    pr = None
                else:
                    pr = self.prayers[_line] = []
            else:
                if pr is None:
                    if not holyday_parse:
                        print("[ERROR]: pray without name: {}".format(line))
                    continue
                _line = line
                if "приложение 2" in _line:
                    st = _line[:12]
                    #print(st)
                    cnt = 0
                    for _ln in PRAYER_GENERIC["generic"]:
                        #print(_ln)
                        if is_similar(st, _ln, 80):
                            if not cnt:
                                _line = _ln
                            cnt += 1
                            #print("Found {} replacement for Troparion: {}\n{}".format(cnt, st, _ln))
                    if not cnt:
                        print("== ERROR ==: replacement for Troparion {} is not found!".format(st))
                elif "см." in _line or "(" in _line:
                    print("== ERROR ==: Replacement should be manually updated")
                pr.append(_line)
                holyday_parse = False

    def set_preaching(self, div):
        self.preaching = []
        for i, line in enumerate(div.lines[0]):
            _line = line.strip()
            if _line:
                self.preaching.append(_line)

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
            "date": self.str_date,
            "title": self.title,
            "saints": self.saints,
            "reading": self.reading,
            "prayers": self.prayers,
            "preaching": self.preaching,
            "trapeza": self.trapeza,
            "trapeza_id": self.trapeza_id,
            "feofan": self.feofan,
        }


class Command(BaseCommand):
    args = ''
    help = 'Parse calendar from calendar.rop.ru'
    leave_locale_alone = True


    def add_arguments(self, parser):
        parser.add_argument(
             '--date',
             dest="date",
             help="parse date in format YYYY-mm-dd (today if None)"
        )
        parser.add_argument(
             '--title',
             dest="title",
             help="cnt lines of Saints lines will be title. Only applicable with --date"
        )

    def __parse_date(self, date, title_lines=0):
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
        parser = Parser()
        parser.feed(inner_part)
        parser.replace_sups()
        reading = parser.extract_reading()
        calendar = Calendar(name)
        calendar.set_title(parser.content[2], lines=title_lines)
        saints = parser.content[2].lines
        calendar.set_saints(saints)
        calendar.set_reading(reading)
        calendar.set_prayers(parser.content[4])
        calendar.set_preaching(parser.content[7])
        #self.stdout.write(str(calendar))
        #for div in parser.content:
        #    self.stdout.write("DIV: {}".format(div))
        with open(os.path.join(settings.CALENDAR_YEAR_DIR,
                               "{}.json".format(name)), "w") as f:
            f.write(ujson.dumps(calendar.to_json()))

    def handle(self, *args, **kwargs):
        today = datetime.datetime.now().date()
        date = kwargs["date"]
        if date is None:
            delta = datetime.timedelta(days=1)
            dt = datetime.date(settings.CALENDAR_YEAR, 7, 28)
            while dt < settings.CALENDAR_PARSE_FINISHED_DATE:
                self.stdout.write("Parsing day: {}".format(dt))
                self.__parse_date(dt)
                dt += delta
        else:
            try:
                dt = datetime.datetime.strptime(date, DATE_FORMAT).date()
            except (TypeError, ValueError):
                dt = today
            try:
                title_lines = int(kwargs["title"])
            except (TypeError, ValueError):
                title_lines = 0
            self.__parse_date(dt, title_lines=title_lines)

