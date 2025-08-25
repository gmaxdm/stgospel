import os
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gospel.models import AgreementGroup, PrayForDiv, PrayFor


class Command(BaseCommand):
    args = ''
    help = 'Copy PrayFor list from one agreement group to another'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
             '--src',
             dest="src_id",
             required=True,
             help="source agreement group ID"
        )
        parser.add_argument(
             '--dest',
             dest="dest_id",
             required=True,
             help="destination agreement group ID"
        )

    def handle(self, *args, **kwargs):
        src_id = kwargs["src_id"]
        dest_id = kwargs["dest_id"]

        try:
            group_src = AgreementGroup.objects.get(id=src_id)
            group_dest = AgreementGroup.objects.get(id=dest_id)
        except AgreementGroup.DoesNotExist:
            raise CommandError("Source or Dest group does not exist")

        _cnt = 0
        for div in PrayForDiv.objects.filter(group_id=src_id):
            div_dest = PrayForDiv.objects.create(
                owner=div.owner,
                group_id=dest_id,
                name=div.name,
                order=div.order,
                root=div.root
            )
            self.stdout.write("PrayForDiv '{}' created with ID {}.".format(div.name, div_dest.id))
            names = []
            for pf in PrayFor.objects.filter(div_id=div.id):
                names.append(PrayFor(
                    div=div_dest,
                    name=pf.name,
                    list_type=pf.list_type,
                    till=pf.till,
                    order=pf.order,
                    deleted=pf.deleted
                ))
            PrayFor.objects.bulk_create(names)
            self.stdout.write("{} PrayFor list names copied for '{}'.".format(len(names), div.name))
            _cnt += 1
        self.stdout.write("------------")
        self.stdout.write("{} PrayForDivs groups of names copied.".format(_cnt))

