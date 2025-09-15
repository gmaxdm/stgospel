import logging
from django.urls import reverse
from django.http import (HttpResponseRedirect, HttpResponseForbidden, JsonResponse,
                         Http404)
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.db import IntegrityError
from django.db.models import Q

from gospel.json import (JsonListView, JsonContextView, LazyEncoder)
from gospel.models import (AgreementGroup, get_today_for_user, OrthodoxCalendar,
                           DATE_DELTA_DAY, DATE_FORMAT)
from authuser.views import (LoginRequired, MySynodikBaseView)
from bible.models import (Book, Chapter, Line, Pray, Volume, VolumeBook,
                          VolumeChapters, VolumeItemChapter, VolumePray,
                          get_norm_book_short_title)
from bible.ref_parser.ref_parser import RefBook
from bible.forms import VolumeCreateForm
from forum.models import DirtyWord


logger = logging.getLogger("django")


class BibleView(JsonListView):
    template_name = "bible/bible.html"
    queryset = Book.objects.all().order_by("order")


class VolumeListView(JsonListView):
    template_name = "volume/list.html"

    def get_queryset(self):
        return Volume.objects.filter(Q(creater_id=self.request.user.id) | Q(public=True))


class PrayView(JsonContextView):
    template_name = "pray/pray.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            try:
                context["pray"] = Pray.objects.get(id=kwargs["id"])
            except KeyError:
                context["pray"] = Pray.objects.get(slug=kwargs["slug"])
            return context
        except Pray.DoesNotExist:
            raise Http404


class PsalterView(MySynodikBaseView):
    template_name = "pray/psalter/main.html"

    def get(self, request, num, *args, **kwargs):
        self.template_name = f"pray/psalter/kathisma{num}.html"
        return super().get(request, num, *args, **kwargs)


class MorningView(MySynodikBaseView):
    template_name = "pray/morning.html"


class CommunionView(JsonContextView):
    template_name = "pray/communion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today_for_user(self.request.user, with_time=True)
        dt = today
        if today.hour >= 12:
            dt += DATE_DELTA_DAY
        calendar = OrthodoxCalendar(date=dt).data
        context["tropar"] = []
        for title, pray in calendar["prayers"].items():
            if "тропар" in title.lower():
                context["tropar"].append((title, pray))
        return context


class KanonAveMariaView(MySynodikBaseView):
    template_name = "pray/kanon_Ave_Maria.html"


class PrayListView(JsonListView):
    template_name = "pray/list.html"
    queryset = Pray.objects.all()


class TroparView(JsonContextView):
    template_name = "pray/pray.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            pk = self.request.GET["id"]
            from stgospel.mongo import MongoDBClient as mongo
            context["pray"] = mongo.get_tropar_by_id(pk)
            try:
                context["pray"]["text"] = "<br/>".join(context["pray"]["text"])
            except KeyError:
                pass
        except (KeyError, ValueError):
            raise Http404
        return context


class MyVolumeListView(LoginRequired, ListView):
    template_name = "volume/list.html"

    def get_queryset(self):
        return Volume.objects.filter(creater_id=self.request.user.id)


class BookView(JsonContextView):
    template_name = "bible/book.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            try:
                book = context["book"] = Book.objects.get(id=kwargs["id"])
            except KeyError:
                book = context["book"] = Book.objects.get(slug=kwargs["slug"])
        except Book.DoesNotExist:
            raise Http404
        context["chapters"] = (Chapter.objects.select_related("book")
                                      .filter(book_id=book.id).order_by('num'))
        return context


class ChapterView(JsonContextView):
    template_name = "bible/chapter.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        num = kwargs["num"]
        try:
            try:
                book = context["book"] = Book.objects.get(id=kwargs["id"])
            except KeyError:
                book = context["book"] = Book.objects.get(slug=kwargs["slug"])
        except Book.DoesNotExist:
            raise Http404
        context["chapters"] = (range(book.chapters)
                                if book.has_foreword
                                else range(1, book.chapters + 1))
        context["num"] = num
        context["lines"] = Line.objects.filter(chapter__book_id=book.id,
                                               chapter__num=num).order_by("num", "id")
        return context


class LinesView(JsonContextView):
    template_name = "bible/lines.html"

    @staticmethod
    def get_lines_filter(query_list):
        _q = Q()
        for kw in query_list:
            _q = _q | Q(**kw)
        return _q

    @staticmethod
    def get_chapters_filter(query_list):
        _chapters = set()
        for kw in query_list:
            _chapters.add(kw["chapter__num"])
        return Q(chapter__num__in=_chapters)

    @staticmethod
    def is_line_selected(query, num):
        try:
            return query["num"] == num
        except KeyError:
            try:
                return query["num__gte"] <= num <= query["num__lte"]
            except KeyError:
                try:
                    return num >= query["num__gte"]
                except KeyError:
                    try:
                        return num <= query["num__lte"]
                    except KeyError:
                        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _get = self.request.GET
        try:
            st = get_norm_book_short_title(_get["b"])
            book = context["book"] = Book.objects.get(short_title=st)
        except (KeyError, IndexError, Book.DoesNotExist):
            raise Http404

        try:
            full_text = int(_get["full"])
        except (KeyError, ValueError):
            full_text = 0

        context["chapters"] = range(1, book.chapters+1)
        _filter = None
        try:
            rb = RefBook(st)
            rb.parse_chapters(_get["r"])
            _filter = rb.chapters
            context["query"] = rb.chapters_query
        except (KeyError, ValueError, IndexError) as err:
            _filter = [{"chapter__num": 1}]
            context["query"] = "Глава 1"
        _lines = (Line.objects.select_related("chapter")
                              .filter(chapter__book_id=book.id))

        if _filter:
            if full_text:
                # chapters filter:
                _lines = _lines.filter(self.get_chapters_filter(_filter))
            else:
                # lines filter:
                _lines = _lines.filter(self.get_lines_filter(_filter))

        context["nums"] = {}
        for line in _lines.order_by("chapter__num", "num", "id"):
            try:
                lt = context["nums"][line.chapter.num]
            except KeyError:
                lt = context["nums"][line.chapter.num] = []

            if full_text:
                # mark line as selected
                line.selected = False
                for kw in _filter:
                    if kw["chapter__num"] == line.chapter.num:
                        line.selected = self.is_line_selected(kw, line.num)
                        if line.selected:
                            break
            lt.append(line)

        context["full_text"] = full_text
        return context


class ChapterVolumeView(JsonContextView):
    template_name = "volume/chapter.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = kwargs["id"]
        chid = kwargs["chid"]
        chapters = []
        for ch in (VolumeItemChapter.objects
                                    .filter(volumechapters_id=pk)
                                    .values("volumechapters__title",
                                            "volumechapters__volume__title",
                                            "lines",
                                            "chapter_id",
                                            "chapter__num",
                                            "chapter__book_id",
                                            "chapter__book__title")):
            context["title"] = ch["volumechapters__title"]
            context["volume"] = ch["volumechapters__volume__title"]
            chapter = {
                "id": ch["chapter_id"],
                "book_id": ch["chapter__book_id"],
                "book": ch["chapter__book__title"],
                "num": ch["chapter__num"],
                "lines": ch["lines"],
            }
            if chid == ch["chapter_id"]:
                context["chapter"] = chapter
            chapters.append(chapter)
        context["chapters"] = chapters
        context["lines"] = Line.objects.filter(chapter_id=chid).order_by("num", "id")
        return context


class VolumeView(JsonContextView):
    template_name = "volume/volume.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context.update(Volume.objects.get(id=kwargs["id"]).get_full_data)
        except (IndexError, Volume.DoesNotExist) as err:
            raise Http404
        return context


class VolumeQueueView(VolumeView):
    template_name = "volume/queue.html"


class VolumeCreateView(LoginRequired, CreateView):
    template_name = "volume/create.html"
    model = Volume
    form_class = VolumeCreateForm

    def get(self, request):
        return render(request, self.template_name, {
            "form": VolumeCreateForm()
        })

    def form_valid(self, form):
        if self.request.method == 'POST':
            volume = Volume.objects.create(title=form.cleaned_data["title"],
                                           creater=self.request.user)
            return HttpResponseRedirect(reverse("volume-edit", kwargs={"id": volume.id }))


class VolumeAccessMixin(View):
    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs.get("id") or request.POST["id"]
            self.volume = Volume.objects.get(id=int(pk),
                                             creater_id=request.user.id)
        except (KeyError, Volume.DoesNotExist, ValueError, TypeError):
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)


class VolumeRemoveView(LoginRequired, VolumeAccessMixin, TemplateView):
    template_name = "volume/remove.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["volume"] = self.volume
        context["agreementgroups"] = AgreementGroup.objects.filter(volume_id=self.volume.id)
        return context

    def post(self, request, *args, **kwargs):
        self.volume.delete()
        return HttpResponseRedirect(reverse('volumes-my'))


class VolumeEditView(LoginRequired, VolumeAccessMixin, TemplateView):
    template_name = "volume/edit.html"

    def post(self, request, *args, **kwargs):
        ret = -1
        try:
            action = request.POST["action"]
            pk = int(request.POST["id"])
            if action == "title":
                title = DirtyWord.clean(request.POST["name"])
                if not DirtyWord.is_empty(title):
                    (Volume.objects.filter(id=pk)
                                   .update(title=title))
                    ret = pk
            elif action == "public":
                (Volume.objects.filter(id=pk)
                               .update(public=request.POST["on"]))
                ret = pk
            elif action == "add_book":
                lt = []
                for _id in request.POST.getlist("book_id[]"):
                    lt.append(VolumeBook(volume_id=pk, book_id=_id))
                VolumeBook.objects.bulk_create(lt)
            elif action == "rem_book":
                (VolumeBook.objects.filter(volume_id=pk,
                                           book_id=request.POST["book_id"])
                                   .delete())
            elif action == "chapter":
                title = DirtyWord.clean(request.POST["name"])
                obj = VolumeChapters.objects.create(volume_id=pk,
                                                    title=title,
                                                    order=request.POST["order"])
                ret = obj.id
            elif action == "title_chapter":
                title = DirtyWord.clean(request.POST["name"])
                if not DirtyWord.is_empty(title):
                    (VolumeChapters.objects.filter(id=request.POST["sub_id"])
                                   .update(title=title))
            elif action == "del_chapter":
                (VolumeItemChapter.objects.filter(volumechapters_id=request.POST["sub_id"])
                                  .delete())
                VolumeChapters.objects.filter(id=request.POST["sub_id"]).delete()
            elif action == "add_chapter":
                try:
                    ln = int(request.POST["len"])
                except (KeyError, TypeError, ValueError):
                    ln = 0
                lt = []
                for i, _id in enumerate(request.POST.getlist("ch_id[]")):
                    lt.append(VolumeItemChapter(volumechapters_id=request.POST["sub_id"],
                                                chapter_id=_id,
                                                order=(ln + i)))
                VolumeItemChapter.objects.bulk_create(lt)
            elif (action == "rem_chapter" or action == "del_line"):
                (VolumeItemChapter.objects.filter(volumechapters_id=request.POST["sub_id"],
                                                  chapter_id=request.POST["ch_id"])
                                          .delete())
            elif action == "add_line":
                try:
                    vic = VolumeItemChapter.objects.get(id=request.POST["sub_id"])
                except VolumeItemChapter.DoesNotExist:
                    raise ValueError

                if vic.add_lines(map(int, [num for num in request.POST.getlist("ln_num[]")])):
                    vic.save()
            elif action == "rem_line":
                try:
                    vic = VolumeItemChapter.objects.get(id=request.POST["sub_id"])
                except VolumeItemChapter.DoesNotExist:
                    raise ValueError

                if vic.del_lines(map(int, [request.POST["ln_num"]])):
                    vic.save()
        except (KeyError, IntegrityError, ValueError, TypeError) as err:
            logger.info(err)
            return JsonResponse({"error": ret})
        return JsonResponse({"ok": ret})

