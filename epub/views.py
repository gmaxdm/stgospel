import tempfile
import datetime
import os
import zipfile
import shutil
import logging

from django.shortcuts import render
from django.http import FileResponse
from django.template.loader import render_to_string
from django.views import View
from django.conf import settings

from gospel.models import get_today, DATE_FORMAT, DATE_DELTA_DAY


logger = logging.getLogger("django")


EPUB_READING_DELTA = 40


class EPubView(View):

    def get(self, request, *args, **kwargs):
        agu = kwargs["group_user"]
        group = agu.group
        isbreak = group.settings.is_break_date()
        if not isbreak and group.settings.end:
            fromdate = group.settings.start
            todate = group.settings.end
        else:
            fromdate = get_today()
            todate = fromdate + datetime.timedelta(days=EPUB_READING_DELTA)
        bookid = "{}-from_{}_to_{}".format(group.id,
                                           fromdate.strftime(DATE_FORMAT),
                                           todate.strftime(DATE_FORMAT))

        dt = fromdate
        pages = []
        breakinside = False
        while dt <= todate:
            if (isbreak and
                group.settings.end < dt < group.settings.bdate):
                breakinside = True
            else:
                rd = group.get_reading(date=dt)
                if rd is None:
                    break
                pages.append(rd)
            dt += DATE_DELTA_DAY
        with tempfile.TemporaryDirectory() as tdir:
            midir = os.path.join(tdir, "META-INF")
            os.makedirs(midir)
            shutil.copy(os.path.join(settings.EPUB_SRC, "META-INF", "container.xml"),
                        os.path.join(midir, "container.xml"))
            shutil.copytree(os.path.join(settings.EPUB_SRC, "css"),
                            os.path.join(tdir, "css"))
            shutil.copytree(os.path.join(settings.EPUB_SRC, "images"),
                            os.path.join(tdir, "images"))
            with open(os.path.join(tdir, "content.opf"), "w") as f:
                f.write(render_to_string("epub/content.opf", {
                    "bookid": bookid,
                    "user": request.user,
                    "pages": pages,
                }))
            with open(os.path.join(tdir, "title.html"), "w") as f:
                f.write(render_to_string("epub/title.html", {
                    "group": group,
                    "break": breakinside,
                }))
            with open(os.path.join(tdir, "toc.ncx"), "w") as f:
                f.write(render_to_string("epub/toc.ncx", {
                    "bookid": bookid,
                    "pages": pages,
                }))
            for page in pages:
                with open(os.path.join(tdir, "{}.html".format(page["name"])), "w") as f:
                    f.write(render_to_string("epub/reading.html", page).replace("<br>", r"<br/>"))
            bookfile = os.path.join(settings.EPUB_ROOT, "{}.epub".format(bookid))
            with zipfile.ZipFile(bookfile, "w") as f:
                f.write(os.path.join(settings.EPUB_SRC, "mimetype"), "mimetype")
            with zipfile.ZipFile(bookfile, "a", zipfile.ZIP_DEFLATED) as f:
                for root, dirs, files in os.walk(tdir):
                    for fl in files:
                        flpath = os.path.join(root, fl)
                        f.write(flpath, os.path.relpath(flpath, tdir))
        response = FileResponse(open(bookfile, "rb"), content_type="application/epub+zip")
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(os.path.basename(bookfile))
        return response

