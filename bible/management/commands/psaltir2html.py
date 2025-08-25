"""
python manage.py psaltir2html

NOTE:
1. kathisma17.html needs to be changed manually:
 - move prayers between lines (before 73, 132),
 - [Sreda] as <p>
2. kathisma20.html - update manually
"""
import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

import bible
from bible.helpers.psalter import SECONDARY_LINES


PSALTIR_FILE = os.path.join(os.path.dirname(bible.__file__),
                            "txt",
                            "psaltir.txt")
PSALTIR_DIR = os.path.join(os.path.dirname(bible.__file__),
                           "templates", "pray", "psalter")
RE_PSALOM = re.compile(r"Псалом (\d+)")
RE_LINE = re.compile(r"(\d+) ([^\d]+)")


class Line:

    def __init__(self, num, text, is_secondary):
        self.num = num
        self.text = text
        self.is_secondary = is_secondary


class Psalom:

    def __init__(self, title, num):
        self.lines = []
        self.title = title
        self.num = num

    def add_line(self, num, text):
        sec_lines = SECONDARY_LINES[self.num-1]
        is_sec = num in sec_lines
        self.lines.append(Line(num, text, is_sec))


class Tropar:

    def __init__(self, title):
        self.title = title
        self.text = []
        self.slava = ""
        self.nine = ""


class Kathisma:

    def __init__(self, title, num):
        self.num = num
        self.title = title
        self.cur_ps = None
        self.psalms1 = []
        self.psalms2 = []
        self.psalms3 = []
        self.tropar = None
        self.pray = ""

    def add_psalom(self, title, num, part):
        self.cur_ps = Psalom(title, num)
        if part == 1:
            self.psalms1.append(self.cur_ps)
        elif part == 2:
            self.psalms2.append(self.cur_ps)
        elif part == 3:
            self.psalms3.append(self.cur_ps)

    def add_line(self, num, text):
        self.cur_ps.add_line(num, text)

    def get_ctx(self):
        ctx = {
            "kathisma": self.title,
            "psalms1": self.psalms1,
            "psalms2": self.psalms2,
            "psalms3": self.psalms3,
            "num": self.num,
            "tropar": self.tropar,
            "pray": self.pray,
        }
        return ctx


class Command(BaseCommand):
    args = ''
    help = 'Import Psaltir from txt to kathisma html files'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        with open(PSALTIR_FILE) as f:
            lines = f.readlines()

        kathismas = []
        psalms_part = 1
        collect_lines = False

        last_kath = None
        for line in lines:
            ln = line.strip()
            if not ln:
                continue

            try:
                if "Кафи́сма" in ln:
                    last_kath = Kathisma(ln, len(kathismas)+1)
                    kathismas.append(last_kath)
                elif "Псалом" in ln:
                    m = RE_PSALOM.match(ln)
                    if not m:
                        continue

                    try:
                        ps_num = int(m.group(1))
                    except ValueError:
                        print("CHAPTER ERROR")
                        print(ln)

                    last_kath.add_psalom(ln, ps_num, psalms_part)
                    collect_lines = True
                elif "Слава:" == ln:
                    psalms_part += 1
                    # end of kathisma:
                    if psalms_part == 4:
                        collect_lines = False
                        psalms_part = 1
                elif "Тропарь" in ln or "Таже тропари" in ln:
                    title, text = ln.split(":", 1)
                    last_kath.tropar = Tropar(title)
                    last_kath.tropar.text.append(text)
                else:
                    if collect_lines:
                        m = RE_LINE.match(ln)
                        if m:
                            for num, text in RE_LINE.findall(ln):
                                try:
                                    n = int(num)
                                except ValueError:
                                    print("LINE ERROR")
                                    print(ln)

                                last_kath.add_line(n, text.strip())
                        else:
                            last_kath.add_line(0, ln)
                    else:
                        if last_kath is None:
                            continue
                        if last_kath.tropar is None:
                            continue

                        # tropar:
                        if ln.startswith("Слава:"):
                            _, text = ln.split(":", 1)
                            last_kath.tropar.slava = text
                        elif ln.startswith("И ныне:"):
                            _, text = ln.split(":", 1)
                            last_kath.tropar.nine = text
                        elif "40" in ln:
                            continue
                        elif last_kath.tropar.slava and last_kath.tropar.nine:
                            last_kath.pray = ln
                        else:
                            last_kath.tropar.text.append(ln)
            except:
                print(ln)
                raise

        # saving kathisma:
        for kath in kathismas:
            ctx = kath.get_ctx()
            st = render_to_string('pray/psalter/kathisma_template.html', ctx)
            k_file = os.path.join(PSALTIR_DIR, f"kathisma{kath.num}.html")
            print(f"writing {k_file}...")
            with open(k_file, "w") as f:
                f.write(st)

