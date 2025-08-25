from django.core.management.base import BaseCommand, CommandError

from bible.models import *


BIBLE_VOLUME_ID = 17

LINES_SUM_PER_DAY = LINES_TEXT_LENGTH // 430


class Command(BaseCommand):
    args = ''
    help = ("Create Bible Year Reading Volume"
            "from Bible Volume contains all books"
            "(except Psaltyr Cercovn)")
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
             '--volume',
             dest="volume",
             help="source volume id"
        )

    def create_volume_item(self, volume, cnt, chapters, s):
        vc = VolumeChapters.objects.create(title="День {}".format(cnt),
                                           volume=volume,
                                           order=cnt)
        for i, c in enumerate(chapters):
            vic = VolumeItemChapter.objects.create(volumechapters_id=vc.id,
                                                   chapter=c, order=i)
        self.stdout.write("День {}, глав: {}, символов: {}\n".format(cnt, len(chapters), s))

    def handle(self, *args, **kwargs):
        _volume_id = kwargs.get("volume") or BIBLE_VOLUME_ID
        v = Volume.objects.get(id=_volume_id)
        data = v.get_full_data
        books = data["books"]

        new_volume = Volume.objects.create(title="За год ({})".format(LINES_SUM_PER_DAY),
                                           creater_id=2)

        lines = (Line.objects.select_related()
                     .filter(chapter__book_id__in=[b.book.id for b in books])
                     .order_by("chapter__book__order", "chapter__num"))
        chapters = (Chapter.objects.select_related()
                           .filter(book_id__in=[b.book.id for b in books])
                           .order_by('book__order'))
        self.stdout.write("============== {} ==============\n".format(LINES_SUM_PER_DAY))
        s = 0
        cnt = 0
        _ch = []
        for ch in chapters:
            _ch.append(ch)
            lines = Line.objects.filter(chapter_id=ch.id)
            s += sum([len(l.text) for l in lines])
            if s >= LINES_SUM_PER_DAY:
                cnt += 1
                self.create_volume_item(new_volume, cnt, _ch, s)
                _ch = []
                s = 0
        if _ch:
            cnt += 1
            self.create_volume_item(new_volume, cnt, _ch, s)

