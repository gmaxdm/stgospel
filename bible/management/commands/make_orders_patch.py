from django.core.management.base import BaseCommand, CommandError


from bible.models import *


class Command(BaseCommand):
    args = ''
    help = ("Add sorting order for Books. "
            "Same as ID before Psaltir; and ID+1 after"
            "to insert Psaltir Tscerkovn. between")
    leave_locale_alone = True

    def handle(self, *args, **kwargs):
        for b in Book.objects.filter(id__lte=22):
            b.order = b.id
            b.save(update_fields=["order"])

        for b in Book.objects.filter(id__gt=22):
            if b.order == 23:
                continue
            b.order = b.id + 1
            b.save(update_fields=["order"])

