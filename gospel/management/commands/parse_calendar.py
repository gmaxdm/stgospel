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
                          split_by_index, is_similar, is_refs_snoska)
from bible.ref_parser.ref_parser import RefParser


SEP_BEGIN = "udiz_koren.txt begin"
SEP_END = "udiz_koren.txt end"
INCLUDE_TAGS = ["b", "strong", "small"]
ENDLINE_TAGS = ["br", "p", "center"]

LINE_ENDS = (".", "!")


rePrTitle = re.compile(r"[\w\s\.,\(\)]+[^:]$")

reAsterix = re.compile(r"\*+")


with open(settings.HOLYDAY_DATA) as f:
    HOLYDAY = ujson.loads(f.read())


with open(settings.PRAYER_GENERIC_DATA) as f:
    PRAYER_GENERIC = ujson.loads(f.read())


class SupLine(str):
    index = []
    sups = []

    #def __str__(self):
    #    return "{} (index: {}, sups: {})".format(super().__str__(),
    #                                             ",".join(map(str, self.index)),
    #                                             ",".join(map(str, self.sups)))


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
        return "\n".join(map(str, self.lines))


class Parser(HTMLParser):
    """ This parser is oriented to parse the following pattern:
        div0: date
        div1: saints, reading (with notes div if exists)
        div2: line (to exclude)
        div3: prayers
        div4: snoski
        div5: line (to exclude)
        div6: preaching
    """
    div_tag = "div"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sups_cnt = 0
        self.catch_sup = False
        self.divs = []
        self.cur_div = None
        self.content = []

    def __parse_sup_data(self, data):
        """ expecting data like '[<cnt>]' - 2022
        """
        return data[1:-1]

    def __remove_asterix_sups(self, data):
        """ expecting data like "** note2"
        """
        i = 0
        for c in data:
            if c == "*":
                i += 1
            elif i and c == " ":
                # including the space after
                i += 1
                break
            else:
                break
        return data[i:]

    def handle_data(self, data):
        if not data:
            return

        if self.cur_div:
            if self.catch_sup:
                #self.cur_div.sups.append(self.__parse_sup_data(data))
                note = self.__remove_asterix_sups(data)
                self.cur_div.add(note)
            else:
                self.cur_div.add(data)

    def handle_starttag(self, tag, attrs):
        if tag == self.div_tag:
            for attr in attrs:
                if attr[0] == "class" and attr[1] == "notes":
                    self.catch_sup = True
            # omit sup div
            #if self.catch_sup:
            #    return

            if self.cur_div:
                # handle not closing prev tags:
                self.cur_div.flush_line()
            self.cur_div = Div()
            self.divs.append(self.cur_div)
        elif tag == "sup":
            self.catch_sup = True
            self.sups_cnt += 1
            idx = sum(map(len, self.cur_div.line))
            self.cur_div.index.append(idx)
        elif tag == "p":
            if self.catch_sup:
                self.sups_cnt += 1
        elif self.cur_div:
            if tag in INCLUDE_TAGS:
                self.cur_div.add("<{}>".format(tag))
            elif tag in ENDLINE_TAGS:
                self.cur_div.flush_line()

    def handle_endtag(self, tag):
        if self.cur_div:
            if tag == self.div_tag:
                # omit sup div
                if self.catch_sup:
                    self.catch_sup = False
                #    return

                self.cur_div.flush_line()
                _div = self.divs.pop()
                try:
                    self.cur_div = self.divs[-1]
                    self.cur_div.add_line(_div)
                except IndexError:
                    self.cur_div = None
                    self.content.append(_div)
            elif tag == "sup":
                self.catch_sup = False
            elif tag in INCLUDE_TAGS:
                self.cur_div.add("</{}>".format(tag))
            elif tag in ENDLINE_TAGS:
                self.cur_div.flush_line()
        else:
            if tag == self.div_tag:
                print("== ERROR ==: closing DIV without start tag!")

    def extract_reading(self):
        lines = []
        reading = []
        for line in self.content[2].lines:
            line = line.replace("_", " ").replace("–", "-")
            rp = RefParser(line)
            if rp.refs:
                _line = replace_readings(rp.refs, line)
                if is_refs_snoska(rp.refs):
                    lines.append(_line)
                else:
                    _refs = split_readings(_line)
                    if _line.count("</a>") != sum([_r.count("</a>") for _r in _refs]):
                        print("== ERROR == reading refs not match links count")
                    reading.append(_refs)
            else:
                lines.append(line)
        self.content[2].lines = lines
        return reading

    def replace_sups_2023(self):
        def __replace_sups(div, sups=None):
            _div = Div()
            _changed = False
            # searching sups:
            _sups = sups
            if _sups is None:
                _idx = 0
                for i, _d in enumerate(div):
                    if isinstance(_d, Div):
                        _sups = _d
                        _idx = i
            if _sups is None:
                return _div, False

            for line in div.lines:
                _ch = False
                if isinstance(line, Div):
                    line.sups = div.sups
                    _d, _ch = __replace_sups(line, sups=_sups)
                    _div.add_line(_d)
                else:
                    _line = line
                    if "*" in line:
                        for _ast in reAsterix.findall(line):
                            _line = _line.replace("*" * len(_ast),
                                                  ' (<small class="text-muted">{}</small>)'
                                                  .format(_sups.lines[len(_ast) - 1]), 1)
                        _ch = True
                    _div.add_line(_line)
                _changed = _changed or _ch

            if sups is None:
                del _div.lines[_idx]

            return _div, _changed

        for i, div in enumerate(self.content[1:6]):
            _div, changed = __replace_sups(div)
            if changed:
                self.content[i+1] = _div

        _div, changed = __replace_sups(self.content[6].lines[0])
        if changed:
            self.content[6].lines[0] = _div

    def replace_sups(self, sups:dict):
        if self.sups_cnt:

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
                                                .format(sups[line.sups[i]]))
                                    _ch = True
                                except (KeyError, IndexError):
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
        for i, line in enumerate(div.lines):
            # prayers title is div tag:
            if isinstance(line, Div):
                _line = str(line).strip()
            # prayers title is p tag uncomment below:
            #if line.strip().endswith(":"):
            #    _line = str(line)
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
                elif 0 and "Тропарь воскресный" in _line:
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
        _div = div.lines[0]
        self.preaching = []
        for i, line in enumerate(_div):
            _line = line.strip()
            if _line:
                rp = RefParser(_line)
                if rp.refs:
                    _line = replace_readings(rp.refs, _line)
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
        #sups = {}
        #for line in parser.content[5]:
        #    k, sp, v = line.partition(" ")
        #    sups[k] = v
        #parser.replace_sups(sups)

        parser.replace_sups_2023()

        reading = parser.extract_reading()
        calendar = Calendar(name)
        calendar.set_title(parser.content[2], lines=title_lines)
        saints = parser.content[2].lines
        calendar.set_saints(saints)
        calendar.set_reading(reading)
        calendar.set_prayers(parser.content[4])
        calendar.set_preaching(parser.content[6])
        #self.stdout.write("reading: {}".format(reading))
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
            dt = datetime.date(settings.CALENDAR_YEAR, 1, 1)
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

