import os

from django.core.management.base import BaseCommand, CommandError
from bible.models import Remark, Book
import bible


PRIM = os.path.join(os.path.dirname(bible.__file__), "prim")
IOV_ID = 21


class Command(BaseCommand):
    args = ''
    help = 'Import Bible Remarks from prim files to MySQL'
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        with open(os.path.join(PRIM, "21_iov_prim.txt")) as f:
            data = f.read()
            Remark.objects.create(book_id=IOV_ID, text=data)
            Book.objects.filter(id=IOV_ID).update(has_notes=True)

