# encoding=utf-8
import os
import re

from django.core.management.base import BaseCommand, CommandError

import bible
from bible.models import *


PSALTIR_FILE = os.path.join(os.path.dirname(bible.__file__),
                            "txt",
                            "psaltir.txt")
RE_PSALOM = re.compile(r"Псалом (\d+)")
RE_LINE = re.compile(r"(\d+) ([^\d]+)")


class Command(BaseCommand):
    args = ''
    help = 'Import Psaltir from txt to MySQL'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        book = Book.objects.create(title="Псалтирь (церковнославянский)",
                                   slug="psaltir-tserkovnoslavianskii",
                                   order=23)
        #print("Creating book")
        with open(PSALTIR_FILE) as f:
            lines = f.readlines()
            chapters_cnt = 0
            lines_cnt = 0
            chapter = None
            for line in lines:
                ln = line.strip()
                if not ln:
                    continue
                if "Псалом" in ln:
                    m = RE_PSALOM.match(ln)
                    if not m:
                        continue
                    try:
                        ch_num = int(m.group(1))
                    except ValueError:
                        print("CHAPTER ERROR")
                        print(ln)
                    if chapter and lines_cnt:
                        chapter.lines = lines_cnt
                        chapter.save(update_fields=["lines"])
                        #print("Lines: {}".format(lines_cnt))
                        lines_cnt = 0
                    chapter = Chapter.objects.create(num=ch_num,
                                                     book=book)
                    #chapter = 2
                    #print("Creating chapter {}".format(ch_num))
                    chapters_cnt += 1
                else:
                    m = RE_LINE.match(ln)
                    if m:
                        for num, text in RE_LINE.findall(ln):
                            try:
                                n = int(num)
                            except ValueError:
                                print("LINE ERROR")
                                print(ln)
                            Line.objects.create(num=n, text=text.strip(),
                                                chapter=chapter)
                            #print("Creating line {}".format(n))
                            lines_cnt += 1
                    elif chapter and (lines_cnt == 0 or (chapter.num == 151 and
                                                         lines_cnt == 1)):
                        Line.objects.create(num=0, text=ln,
                                            chapter=chapter)
                        #print("Creating line 0")
                        lines_cnt += 1
            #print("Lines: {}".format(lines_cnt))
            #print("Total chapters: {}".format(chapters_cnt))
            book.chapters = chapters_cnt
            book.save(update_fields=["chapters"])
            chapter.lines = lines_cnt
            chapter.save(update_fields=["lines"])

