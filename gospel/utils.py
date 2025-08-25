import os
import re
import ujson
import datetime
import string
from unidecode import unidecode
from urllib.parse import quote
from html.parser import HTMLParser

from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings

from gospel.models import DATE_FORMAT
from bible.models import BOOK_SHORT_TITLES, BOOK_SHORT_ALIAS


LINES_URL = reverse("lines")

RE_READING = re.compile(r"([^<>\(\)]+(<a[^>]+>[^<>]+<\/a>\s*)*(\(<small[^>]+>.+<\/small>\))?[.,;]?)")


class CleanTagsParser(HTMLParser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []

    def handle_data(self, data):
        self.data.append(data)

    @property
    def text(self):
        return "".join(self.data)


def clean_tags(line):
    _ctp = CleanTagsParser()
    _ctp.feed(line)
    return _ctp.text


def reading_link(m):
    """
    :type m: MatchReading
    """
    book = m.book.book
    # replacing need to keep cap words
    short_title = string.capwords(
                        slugify(unidecode(book.strip())).replace("-", " ")
                    ).replace(" ", "-")
    _st = short_title.lower()
    if _st not in BOOK_SHORT_TITLES:
        try:
            _ = BOOK_SHORT_ALIAS[_st]
        except KeyError:
            print("== ERROR ==: Reading book's short title is not found: {}"
                  .format(_st))
            return m.match
    return ' <a href="{}">{}</a>'.format("{}?b={}&r={}&full=1".format(LINES_URL,
                                                                      quote(short_title),
                                                                      quote(m.book.chapters_query)),
                                         m.match)


def split_readings(line):
    #for m in RE_READING.finditer(line):
    #    print(m.groups())
    return [m.group(0).strip() for m in RE_READING.finditer(line)]


def replace_readings(refs, line):
    _line = line
    for m in refs:
        st = m.match
        link = reading_link(m)
        _cnt = _line.count(st)
        if _cnt == 1:
            _line = _line.replace(st, link)
        else:
            _line = re.sub('{}(?![\<\.])'.format(st), link, _line)
    return _line


def is_refs_snoska(refs):
    """ Expect snoska is wrapped by <small ...></small>.
        Cut <small> span and search in rest string.
    """
    for r in refs:
        line = r.line
        cutted = re.sub("<small[^>]*>.*</small>", "", line)
        if r.match in cutted:
            return False
    return True


def split_by_index(line, idx):
    """
    :type line: str
    :type idx: list
    :rtype: [str]
    """
    res = []
    st = 0
    for _idx in idx:
        res.append(line[st:_idx])
        st = _idx
    res.append(line[st:])
    return res


def __is_similar(st1, st2, percent):
    """ is st1 similar with st2 per each char
        for about percent percents
    """
    match_cnt = 0
    shift = 0
    i = 0
    while i < len(st1) and i + shift < len(st2):
        if st1[i] == st2[i + shift]:
            match_cnt += 1
            i += 1
        elif shift < 2:
            #print("try with shift")
            shift += 1
        else:
            i += 1
    prc = match_cnt * 100 // len(st1)
    #print(prc)
    return prc > percent


def is_similar(st1, st2, percent):
    if __is_similar(st1, st2, percent):
        return True
    #print("try reverse")
    return __is_similar(st2, st1, percent)

