import os
import re
from unidecode import unidecode

from django.db.utils import DataError
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

import bible
from bible.models import *


TXT = os.path.join(os.path.dirname(bible.__file__), "txt")
RE_LINE = re.compile(r"(\d+)? ?(.*)")

IGNORE_LIST = ('psaltir.txt',)


class Command(BaseCommand):
    args = ''
    help = 'Import Bible from txt files to MySQL'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        for filename in sorted(os.listdir(TXT)):
            if filename in IGNORE_LIST:
                continue

            with open(os.path.join(TXT, filename)) as f:
                lines = f.readlines()
                titleline = lines[1]
                title = titleline.replace("==", "").strip()
                if len(title) < 3:
                    print("!!! {} !!!".format(title))
                book = Book.objects.create(title=title,
                                           slug=slugify(unidecode(title)))
                chapters_cnt = 0
                lines_cnt = 0
                for line in lines[3:]:
                    ln = line.strip()
                    if not ln:
                        continue
                    if ln.startswith("==="):
                        try:
                            ch_num = int(ln.replace("===", "").strip())
                        except ValueError:
                            print("CHAPTER ERROR")
                            print(filename)
                            print(ln)
                        if lines_cnt:
                            chapter.lines = lines_cnt
                            chapter.save(update_fields=["lines"])
                            lines_cnt = 0
                        chapter = Chapter.objects.create(num=ch_num,
                                                         book=book)
                        chapters_cnt += 1
                        if ch_num == 0:
                            book.has_foreword = True
                            book.save(update_fields=["has_foreword"])
                    else:
                        m = RE_LINE.match(ln)
                        if m:
                            num, text = m.groups()
                            if len(text) > 4000:
                                print("LONG TEXT: {}".format(len(text)))
                                print(filename)
                                print(ln)
                            try:
                                n = int(num or 0)
                            except ValueError:
                                print("LINE ERROR")
                                print(filename)
                                print(ln)
                            Line.objects.create(num=n, text=text,
                                                chapter=chapter)
                            lines_cnt += 1
                book.chapters = chapters_cnt
                book.save(update_fields=["chapters"])
                chapter.lines = lines_cnt
                chapter.save(update_fields=["lines"])

