import logging
import random
from unidecode import unidecode

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings

from authuser.models import User
from bible.ref_parser.ref_parser import rim2arab


logger = logging.getLogger("django")


BOOKS = 78
CHAPTERS = 1363
LINES = 37188
LINES_TEXT_LENGTH = 4014599

NON_CANONICAL_IDS = (17, 18, 19, 26, 27, 31, 32, 47, 48, 49, 50)

BOOK_SHORT_TITLES = {
    'byt': 1,
    'iskh': 2,
    'vtor': 5,
    '1-tsar': 9,
    '2-tsar': 10,
    '3-tsar': 11,
    '2-par': 14,
    'ps': 22,
    'pritch': 23,
    'ekkl': 24,
    'solom': 26,
    'iis': 27,
    'is': 28,
    'iez': 33,
    'os': 35,
    'ioil': 36,
    'zakh': 45,
    'mal': 46,
    'mf': 51,
    'mk': 52,
    'lk': 53,
    'in': 54,
    'deian': 55,
    'iak': 56,
    '1-pet': 57,
    '2-pet': 58,
    '1-in': 59,
    '2-in': 60,
    '3-in': 61,
    'iud': 62,
    'rim': 63,
    '1-kor': 64,
    '2-kor': 65,
    'gal': 66,
    'ef': 67,
    'flp': 68,
    'kol': 69,
    '1-sol': 70,
    '2-sol': 71,
    '1-tim': 72,
    '2-tim': 73,
    'tit': 74,
    'flm': 75,
    'evr': 76,
    'apok': 77,
    'psts': 78,
}

BOOK_SHORT_ALIAS = {
    "matfeia": "mf",
    "luki": "lk",
    "ioanna": "in",
    "marka": "mk",
    "deia": "deian",
    "efes": "ef",
    "1-fes": "1-sol",
    "fes": "1-sol",
    "prit": "pritch",
    "iskh": "is",
    "prem": "solom",
    "ev": "evr",
    "fil": "flp",
    "2-fes": "2-sol",
    "mr": "mk",
    "otkr": "apok",
}


def get_norm_book_short_title(title):
    st = title.replace(" ", "-").replace("_", "-").lower()
    try:
        st = BOOK_SHORT_ALIAS[st]
    except KeyError:
        pass
    return st


class Book(models.Model):
    title = models.CharField(max_length=100)
    short_title = models.CharField(max_length=10)
    slug = models.SlugField(max_length=120, unique=True)
    chapters = models.PositiveSmallIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    has_foreword = models.BooleanField(default=False)
    has_notes = models.BooleanField(default=False)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.get_title()

    def to_json(self):
        return {
            "id": self.id,
            "title": self.get_title(),
            "short": self.short_title,
            "chapters": self.chapters,
            "has_foreword": self.has_foreword,
            "has_notes": self.has_notes,
            #"chapters": [ch for ch in (Chapter.objects
            #                                  .filter(book_id=self.id)
            #                                  .order_by("num"))],
        }

    def is_canonical(self):
        return self.id not in NON_CANONICAL_IDS

    def get_title(self):
        _canon = "" if self.is_canonical() else "*"
        return f"{self.title}{_canon}"


class Remark(models.Model):
    text = models.TextField()
    book = models.ForeignKey(Book, models.CASCADE)


class Chapter(models.Model):
    num = models.PositiveSmallIntegerField()
    book = models.ForeignKey(Book, models.CASCADE)
    lines = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "Chapter {}".format(self.num)

    def to_json(self):
        return {
            "id": self.id,
            "num": self.num,
            "book_id": self.book_id,
            "book_title": self.book.title,
            "lines": self.lines,
        }


class LinesManager(models.Manager):
    def get_random_quote(self):
        """Returns random line from books:
        - Pritchi-Solomona (23)
        - Kniga-Ekkleziasta (24)
        - Kniga-Premudrosti-Solomona (26)
        - Kniga-Premudrosti-Iisusa-Syna-Sirakhova (27)
        """
        return (self.select_related("chapter", "chapter__book")
                    .filter(num__gt=0,
                            chapter__book_id__in=[23, 24, 26, 27])
                    .order_by("?"))[:1]

    def get_random_chapter(self):
        ch_id = random.randint(1, CHAPTERS)
        return (self.select_related("chapter", "chapter__book")
                    .filter(chapter_id=ch_id).order_by("id"))


class Line(models.Model):
    num = models.PositiveSmallIntegerField()
    text = models.CharField(max_length=4000)
    chapter = models.ForeignKey(Chapter, models.CASCADE)

    objects = LinesManager()

    def __str__(self):
        return "{} {}".format(self.num, self.text)

    def to_json(self):
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "num": self.num,
            "text": self.text,
        }


class Pray(models.Model):
    title = models.CharField("Название молитвы", max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    text = models.TextField()
    mdate = models.DateTimeField(auto_now=True)
    cdate = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Молитва"
        verbose_name_plural = "Молитвы"

    def __str__(self):
        return self.title

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
        }

    def save(self, *args, **kwargs):
        self.slug = slugify(unidecode(self.title))
        super().save(*args, **kwargs)


class QueueItem:

    def __init__(self, pk, title="", books=None, chapters=None, lines=None):
        """
            books: list of tuples (book, nums:range)
            chapters: chapters (see ch_col items)
            lines: [{
                        "id": ch["volumeitemline__line"],
                        "chapter_id": ch["volumeitemline__line__chapter_id"],
                        "chapter_num": ch["volumeitemline__line__chapter__num"],
                        "book": ch["volumeitemline__line__chapter__book__title"],
                        "num": ch["volumeitemline__line__num"],
                        "text": ch["volumeitemline__line__text"],
                        "order": ch["volumeitemline__order"],
                    }]
        """
        self.id = pk
        self.title = title
        self.books = books
        self.chapters = chapters
        self.lines = lines

    @property
    def item(self):
        if not hasattr(self, "_item"):
            self._item = []
            if self.books:
                _f_args = []
                _f_kwargs = {}
                if self.books:
                    if len(self.books) == 1:
                        _f_kwargs["chapter__book_id"] = self.books[0][0].id
                        _f_kwargs["chapter__num__in"] = self.books[0][1]
                    else:
                        _q = Q()
                        for book, nums in self.books:
                            _q = _q | (Q(chapter__book_id=book.id) &
                                       Q(chapter__num__in=nums))
                        _f_args.append(_q)
                grouped = {}
                ch_id = 0
                b_id = 0
                k = 0
                for i, ln in enumerate(Line.objects.filter(
                                                *_f_args, **_f_kwargs)
                                           .values("id", "num", "text",
                                                   "chapter_id", "chapter__num",
                                                   "chapter__book_id",
                                                   "chapter__book__title")
                                           .order_by("id")):
                    if ch_id != ln["chapter_id"] or b_id != ln["chapter__book_id"]:
                        ch_id = ln["chapter_id"]
                        b_id = ln["chapter__book_id"]
                        k = i
                    try:
                        ch = grouped[k]
                    except KeyError:
                        ch = grouped[k] = {
                            "book": ln["chapter__book__title"],
                            "num": ln["chapter__num"],
                            "lines": [],
                        }
                    ch["lines"].append({
                        "id": ln["id"],
                        "chapter_id": ln["chapter_id"],
                        "chapter_num": ln["chapter__num"],
                        "book": ln["chapter__book__title"],
                        "num": ln["num"],
                        "text": ln["text"],
                        "order": i,
                    })
                for k in sorted(grouped.keys()):
                    self._item.append(grouped[k])
            if self.chapters:
                for chapter in self.chapters:
                    _lines = []
                    _book = None
                    _num = 0
                    for i, ln in enumerate(Line.objects.filter(
                                                    chapter_id=chapter["id"])
                                               .values("id", "num", "text",
                                                       "chapter_id", "chapter__num",
                                                       "chapter__book_id",
                                                       "chapter__book__title")
                                               .order_by("id")):
                        _book = ln["chapter__book__title"]
                        _num = ln["chapter__num"]
                        _lines.append({
                            "id": ln["id"],
                            "chapter_id": ln["chapter_id"],
                            "chapter_num": ln["chapter__num"],
                            "book": ln["chapter__book__title"],
                            "num": ln["num"],
                            "text": ln["text"],
                            "order": i,
                        })
                    self._item.append({
                        "book": _book,
                        "num": _num,
                        "lines": _lines,
                    })
            if self.lines is not None:
                self._item.append({
                    "book": None,
                    "num": None,
                    "lines": self.lines,
                })
        return self._item

    @property
    def partition(self):
        if not hasattr(self, "_partition"):
            lt = self.item
            cnt = len(lt)
            if cnt == 1:
                self._partition = (lt, [], [])
            elif cnt == 2:
                self._partition = ([lt[0]], [lt[1]], [])
            elif cnt == 3 or cnt == 4:
                self._partition = ([lt[0]], [lt[1]], lt[2:])
            elif cnt == 5 or cnt == 6 or cnt == 7:
                self._partition = (lt[:2], lt[2:4], lt[4:])
            else:
                self._partition = (lt[:3], lt[3:6], lt[6:])
        return self._partition


class Volume(models.Model):
    title = models.CharField("Название цикла чтения", max_length=255)
    creater = models.ForeignKey(User, models.SET_NULL, null=True, blank=True)
    public = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    mdate = models.DateTimeField("Дата изменения", auto_now=True)
    cdate = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Сборник"
        verbose_name_plural = "Сборники"

    def __str__(self):
        return self.title

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "creater": self.creater_id,
            "public": self.public,
            "hidden": self.hidden,
        }

    @property
    def get_full_data(self):
        if not hasattr(self, "_fulldata"):
            self._fulldata = {
                "volume": self,
                "books": (VolumeBook.objects
                                    .select_related("book")
                                    .filter(volume_id=self.id)
                                    .order_by("order", "book_id")),
            }
            d = self._fulldata["ch_col"] = {}
            for ch in (VolumeChapters.objects
                                     .filter(volume_id=self.id)
                                     .values("id", "title",
                                             "volumeitemchapter__id",
                                             "volumeitemchapter__lines",
                                             "volumeitemchapter__chapter",
                                             "volumeitemchapter__chapter__num",
                                             "volumeitemchapter__chapter__book_id",
                                             "volumeitemchapter__chapter__book__title",
                                             "volumeitemchapter__chapter__book__short_title",
                                             "volumeitemchapter__order")
                                     .order_by("volumeitemchapter__order",
                                               "volumeitemchapter__id")):
                try:
                    lt = d[ch["id"]]
                except KeyError:
                    lt = d[ch["id"]] = {
                        "id": ch["id"],
                        "title": ch["title"],
                        "chapters": [],
                    }
                if ch["volumeitemchapter__chapter"]:
                    lt["chapters"].append({
                        "id": ch["volumeitemchapter__chapter"],
                        "lines": ch["volumeitemchapter__lines"],
                        "lines_url": VolumeItemChapter.lines_url(
                            ch["volumeitemchapter__chapter__book__short_title"],
                            ch["volumeitemchapter__chapter__num"],
                            ch["volumeitemchapter__lines"],
                        ),
                        "book_id": ch["volumeitemchapter__chapter__book_id"],
                        "book_title": ch["volumeitemchapter__chapter__book__title"],
                        "num": ch["volumeitemchapter__chapter__num"],
                        "order": ch["volumeitemchapter__order"],
                    })
        return self._fulldata

    def queue(self, step=1):
        """ step used for books automated volumes creating
            when splitting chapters
            order in this case is defined by lines ids by default
        """
        data = self.get_full_data
        pk = 1
        # 1. Automated splitting by chapters:
        _prev = 0
        books = []
        for vb in data["books"]:
            i = 0 if vb.book.has_foreword else 1
            _cnt = vb.book.chapters + i
            while i < _cnt:
                j = (i or 1) + step
                if _prev:
                    j -= _prev
                _r = range(_cnt)[i:j]
                if j > _cnt:
                    if _prev:
                        books.append((vb.book, _r))
                    else:
                        books = [(vb.book, _r)]
                    _prev += len(_r)
                    break
                if _prev:
                    books.append((vb.book, _r))
                    _prev = 0
                else:
                    books = [(vb.book, _r)]
                i = j
                yield QueueItem(pk, books=books)
                pk += 1
        if _prev:
            yield QueueItem(pk, books=books)
            pk += 1
        # 2. QueueItem contains chapters in arbitrary order
        for vch in data["ch_col"].values():
            #ids = [ch["id"] for ch in vch["chapters"]]
            #if len(ids):
            if vch["chapters"]:
                #yield QueueItem(pk, title=vch["title"], chapters=ids)
                yield QueueItem(pk, title=vch["title"], chapters=vch["chapters"])
                pk += 1

    def __get_reading(self, idx=0, step=1):
        i = 0
        iterate = True
        while iterate:
            for qi in self.queue(step=step):
                if i == idx:
                    iterate = False
                    break
                i += 1
        return qi

    def get_reading(self, idx=0, step=1):
        queue = list(self.queue(step=step))
        if not queue:
            return QueueItem(0)
        return queue[idx % len(queue)]


class VolumeBook(models.Model):
    volume = models.ForeignKey(Volume, models.CASCADE)
    book = models.ForeignKey(Book, models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "{}. {}".format(self.order, self.book.title)

    def to_json(self):
        return self.book.to_json()

    class Meta:
        unique_together = ("volume", "book")
        ordering = ("order",)


class VolumeChapters(models.Model):
    title = models.CharField("Название собрания глав", max_length=50)
    volume = models.ForeignKey(Volume, models.CASCADE)
    chapters = models.ManyToManyField(Chapter, through="VolumeItemChapter")
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return "{}. {}".format(self.order, self.title)

    def to_json(self):
        return {
            "id": self.id,
            "volume_id": self.volume_id,
            "title": self.title,
        }

    class Meta:
        ordering = ("order",)


class VolumeItemChapter(models.Model):
    """ by default use all lines from a chapter
        if lines is not empty use the ordered list of nums
    """
    volumechapters = models.ForeignKey(VolumeChapters, models.CASCADE)
    chapter = models.ForeignKey(Chapter, models.CASCADE)
    lines = models.CharField(default="", max_length=600)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("volumechapters", "chapter")

    @staticmethod
    def lines_url(book_short_title, chapter_num, lines):
        return reverse("lines") + f"?b={book_short_title}&r={chapter_num},{lines}&full=1"

    @staticmethod
    def get_lines_nums(lines_str):
        """ returns ordered list of nums
        """
        if lines_str == "":
            return []

        _s = set()
        for part in lines_str.split(","):
            try:
                s, e = part.split("-")
                try:
                    s = int(s)
                    e = int(e)
                except ValueError:
                    continue

                if s == e:
                    s_add(s)
                elif e > s:
                    for i in range(s, e+1):
                        _s.add(i)
            except (ValueError, IndexError):
                # not a range
                try:
                    _s.add(int(part))
                except ValueError:
                    continue
        return sorted(list(_s))

    def add_lines(self, lines):
        _s = set(VolumeItemChapter.get_lines_nums(self.lines))
        for l in lines:
            _s.add(l)
        is_equal = _s == set(VolumeItemChapter.get_lines_nums(self.lines))
        if is_equal:
            return False

        self.lines = ",".join(_s)
        return True

    def del_lines(self, lines):
        _s = set(VolumeItemChapter.get_lines_nums(self.lines))
        for l in lines:
            try:
                _s.remove(l)
            except KeyError:
                pass

        is_equal = _s == set(VolumeItemChapter.get_lines_nums(self.lines))
        if is_equal:
            return False

        self.lines = ",".join(_s)
        return True


class VolumePray(models.Model):
    volume = models.ForeignKey(Volume, models.CASCADE)
    pray = models.ForeignKey(Pray, models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("volume", "pray")

