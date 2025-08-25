import os
import sys
import yaml

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bible.models import (Book, Chapter, Line, Volume, VolumeChapters,
                          VolumeItemChapter,
                          BOOKS, CHAPTERS)
from year_bible_plans.parsers import *


BIBLE_PLANS_DIR = os.path.join(settings.BASE_DIR, "year_bible_plans")
CONFIG_PATH = os.path.join(BIBLE_PLANS_DIR, "config.yaml")


def read_yaml(filename):
    with open(filename) as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)


class Command(BaseCommand):
    args = ''
    help = ("Create Bible Year Reading Volumes"
            "by Plans defined in config.yaml")
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument(
             '--plan',
             dest="plan",
             help="plan name from config.yaml"
        )

    def create_volume_item(self, volume, cnt, chapters):
        vc = VolumeChapters.objects.create(title=f"День {cnt}",
                                           volume=volume,
                                           order=cnt)
        for i, c in enumerate(chapters):
            vic = VolumeItemChapter.objects.create(volumechapters_id=vc.id,
                                                   chapter=c, order=i)
        self.stdout.write("День {}, глав: {}\n".format(cnt, len(chapters)))

    def handle(self, *args, **kwargs):
        plan_name = kwargs.get("plan")
        if not plan_name:
            return

        config = read_yaml(CONFIG_PATH)
        try:
            plan_config = config[plan_name]
        except KeyError:
            print(f"plan with name '{plan_name}' is not available in config")
            sys.exit(0)

        try:
            parser_name = plan_config["parser"]
            klass = globals()[parser_name]
            parser = klass()
        except KeyError:
            print(f"parser with name '{parser_name}' is not available in config")
            sys.exit(0)

        with open(os.path.join(BIBLE_PLANS_DIR, plan_config['filename'])) as f:
            volume = Volume.objects.create(title=plan_config['name'],
                                           creater_id=2)
            cnt = 1
            for line in f:
                lt = parser.parse_item(line)
                if lt:
                    # creating chapter container:
                    vc = VolumeChapters.objects.create(title=f"День {cnt}",
                                                       volume=volume,
                                                       order=cnt)
                    # [(book id, chapter num, [lines range])...]
                    for i, tp in enumerate(lt):
                        book_id, chapter_num, lines = tp
                        chapter = Chapter.objects.get(book_id=book_id,
                                                      num=chapter_num)
                        _lines = ""
                        if lines:
                            _lines = "-".join([str(lines[0]), str(lines[1])])
                        VolumeItemChapter.objects.create(
                            volumechapters_id=vc.id,
                            lines=_lines,
                            chapter=chapter, order=i)
                    cnt += 1

        _ids = parser.validate_title_map()
        print(_ids)

