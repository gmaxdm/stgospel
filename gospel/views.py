#coding=utf-8
import logging
import datetime
import calendar
import ujson

from django.shortcuts import render
from django.urls import reverse
from django.http import (HttpResponse, HttpResponseRedirect, HttpResponseForbidden,
                         JsonResponse, HttpResponseNotFound)
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views import View
from django.utils.crypto import get_random_string
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import login as auth_login

from authuser.models import (User, RE_EMAIL, ConfirmState, sort_querylist)
from authuser.views import send_mail
from gospel.models import (AgreementGroup, AgreementGroupUser, Settings,
                           PrayGroup, PrayForDiv, PrayFor, DATE_FORMAT,
                           History, OrthodoxCalendar, get_today_for_user,
                           DATE_DELTA_DAY, DATE_DELTA_DAY_13, ROLES)
from gospel.json import JsonContextView
from gospel.forms import GroupCreateForm
from bible.models import Line, Volume, VolumeBook, Book


logger = logging.getLogger("django")


def get_int(request, param):
    try:
        return int(request.GET[param])
    except (KeyError, TypeError, ValueError):
        return None


def group_access(f):
    def _check(request, *args, **kwargs):
        try:
            pk = kwargs.get("id") or request.POST["id"]
            agu = (AgreementGroupUser.objects
                                     .select_related("group")
                                     .get(group_id=pk,
                                          user_id=request.user.id,
                                          deleted=None))
            #if agu.role != "A":
            #    messages.error(request, "Вы не можете редактировать, "
            #                            "пожалуйста, обратитесь к администратору")
            #    return HttpResponseRedirect(reverse("main"))
            kwargs["group_user"] = agu
            return f(request, *args, **kwargs)
        except (KeyError, AgreementGroupUser.DoesNotExist):
            return HttpResponseForbidden()
    return _check


def group_exist(f):
    def _check(request, *args, **kwargs):
        try:
            pk = request.GET["g"] or request.POST["g"]
            group = AgreementGroup.objects.get(link=pk)
            kwargs["group_user"] = group
            if request.user.is_authenticated:
                kwargs["can_join"] = True
                try:
                    agu = (AgreementGroupUser.objects
                                             .get(group_id=group.id,
                                                  user_id=request.user.id))
                    kwargs["can_join"] = agu.deleted
                except AgreementGroupUser.DoesNotExist:
                    pass
            return f(request, *args, **kwargs)
        except (KeyError, AgreementGroup.DoesNotExist):
            return HttpResponseRedirect(reverse("main"))
    return _check


def main(request):
    today = get_today_for_user(request.user)
    orth_cal = OrthodoxCalendar(date=today)
    return render(request, "main.html", {
        "quote": Line.objects.get_random_quote(),
        "calendar": orth_cal.data,
        "next": orth_cal.find_next_holiday(),
        "today": today,
        "today_old": today - DATE_DELTA_DAY_13,
        "prevdays": range(30, 0, -1),
        "nextdays": range(1, 30),
    })


class TroparionView(JsonContextView):
    template_name = "troparion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today_for_user(self.request.user)
        context["calendar"] = OrthodoxCalendar(date=today).data
        context["today"] = today
        try:
            srch = self.request.GET["search"]
            context["srch"] = srch
            if len(srch) < 3:
                raise ValueError
            from stgospel.mongo import MongoDBClient as mongo
            context["troparions"] = mongo.get_troparions(srch)
        except (KeyError, ValueError):
            pass
        return context


class CalendarMonthView(JsonContextView):
    """ View for Month Calendar
        only for Json requests
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today_for_user(self.request.user)
        day = get_int(self.request, "d")
        month = get_int(self.request, "m")
        if month is None:
            month = today.month
        year = get_int(self.request, "y")
        if year is None:
            year = today.year
        context["m"] = month
        context["d"] = day or 0
        context["c"] = []
        cal = calendar.Calendar()
        for d in cal.itermonthdates(year, month):
            orth_cal = OrthodoxCalendar(date=d)
            data = orth_cal.data
            if not data:
                continue

            context["c"].append({
                "date": d,
                "title": data["title"],
                "trapeza": data["trapeza"],
                "trapeza_id": data["trapeza_id"],
                "saints": data["saints"],
                "easter": data.get("easter"),
                "rip": data.get("rip"),
                "carnival": data.get("carnival"),
                "twelve": data.get("twelve"),
            })
        return context


class CalendarView(JsonContextView):
    template_name = "calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date = datetime.date(year=kwargs["year"],
                             month=kwargs["month"],
                             day=kwargs["day"])
        today = get_today_for_user(self.request.user)
        context["today"] = date
        context["yesterday"] = date - DATE_DELTA_DAY
        context["yesterday_old"] = context["yesterday"] - DATE_DELTA_DAY_13
        context["tomorrow"] = date + DATE_DELTA_DAY
        context["tomorrow_old"] = context["tomorrow"] - DATE_DELTA_DAY_13
        context["today_old"] = date - DATE_DELTA_DAY_13
        orth_cal = OrthodoxCalendar(date=date)
        context["calendar"] = orth_cal.data
        context["next"] = orth_cal.find_next_holiday()
        context["shft"] = (date - today).days * 24
        return context


class CalendarShiftView(JsonContextView):
    template_name = "calendar.html"
    direction = 1
    json_only = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today_for_user(self.request.user)
        try:
            days = self.direction * int(kwargs["days"])
            if abs(days) > 30:
                raise ValueError
            date = today + datetime.timedelta(days=days)
        except (ValueError, KeyError, TypeError):
            date = today
        orth_cal = OrthodoxCalendar(date=date)
        context["calendar"] = orth_cal.data
        context["today"] = date
        context["old"] = date - DATE_DELTA_DAY_13
        return context


class GroupView(JsonContextView):
    template_name = "groups/group.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = kwargs["group_user"].group
        context["can_edit"] = kwargs["group_user"].perm_edit()
        context["data"] = group.get_full_data
        settings = context["data"]["settings"]
        today = get_today_for_user(self.request.user)
        context["date"] = group.get_date(today)
        context["isbreak"] = False
        context["insidebreak"] = False
        if settings.is_break_date():
            context["isbreak"] = settings.bdate > today
            context["insidebreak"] = settings.end < today < settings.bdate
        context["prevdate"] = group.get_prevdate(today)
        context["prevprevdate"] = group.get_prevprevdate(today)
        context["nextdate"] = group.get_nextdate(today)
        context["otherdate"] = context["nextdate"]
        if context["otherdate"] is None:
            if group.is_finished(today):
                context["otherdate"] = settings.end
            else:
                context["otherdate"] = settings.start
        context["history"] = (History.objects.select_related("user")
                                     .filter(group_id=group.id)
                                     .order_by("-id")[:12])
        return context


class GroupMembersView(TemplateView):
    template_name = "groups/members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = kwargs["group_user"].group
        context["group_user"] = kwargs["group_user"]
        context["group"] = group
        context["users"] = (AgreementGroupUser.objects
                                              .select_related("user")
                                              .filter(group_id=group.id))
        return context


class GroupInviteView(TemplateView):
    template_name = "groups/invite.html"

    def post(self, request, *args, **kwargs):
        agu = kwargs["group_user"]
        group = agu.group
        if agu.perm_admin():
            subject = "Приглашение в группу " + group.name
            try:
                invite = request.POST["invite"]
                users = {u.email.lower(): u for u in User.objects.all()}
                yet = {u.user_id: u
                        for u in AgreementGroupUser.objects.filter(group_id=group.id)}
                cnt = 0
                for ln in invite.split(",")[:5]:
                    user = ln.strip()
                    first_name = None
                    last_name = None
                    m = RE_EMAIL.match(user)
                    if m:
                        first_name, _, last_name, email = m.groups()
                    else:
                        email = user
                    try:
                        validate_email(email)
                    except ValidationError:
                        continue
                    try:
                        user = users[email.lower()]
                        if user.id in yet and yet[user.id].deleted is None:
                            continue
                    except KeyError:
                        user = User(first_name=first_name or "",
                                    last_name=last_name or "",
                                    username=email,
                                    email=email)
                        user.set_password(get_random_string(8))
                        user.save()
                    confirmstr = get_random_string(32)
                    data = ujson.dumps({"user_id": user.id, "group_id": group.id})
                    ConfirmState(confirmstr=confirmstr, data=data, invite=True).save()
                    try:
                        send_mail(user.email, subject, "letters/invite_letter.html", {
                            "user": user,
                            "group": group,
                            "confirmstr": confirmstr,
                        })
                        cnt += 1
                    except:
                        continue
                messages.success(request,
                                 "Приглашение отправлено {} участникам".format(cnt))
            except KeyError:
                pass
        else:
            messages.error(request,
                           "только Администраторы группы могут приглашать участников")
        return HttpResponseRedirect(reverse("group-invite", kwargs={"id": group.id }))


class InviteConfirmView(View):

    @never_cache
    def get(self, request):
        try:
            confirmstr = request.GET['t']
            state = ConfirmState.objects.get(confirmstr=confirmstr)
            data = ujson.loads(state.data)
            state.delete()
            try:
                user = User.objects.get(id=data["user_id"])
                group = AgreementGroup.objects.get(id=data["group_id"])
                agu, crtd = (AgreementGroupUser.objects
                                               .get_or_create(user_id=user.id,
                                                              group_id=group.id))
                if crtd:
                    History.objects.create(user=user, group=group, action="new_member")
                else:
                    if agu.deleted is not None:
                        agu.deleted = None
                        agu.save(update_fields=["deleted"])
                auth_login(request, user)
                messages.success(request,
                                 "Вы успешно добавлены в группу {}!".format(group.name))
                return HttpResponseRedirect(reverse("main"))
            except IntegrityError:
                pass
            except User.DoesNotExist:
                messages.error(request, "Пользователя с таким email в системе не существует")
            except AgreementGroup.DoesNotExist:
                messages.error(request, "Чтение не существует или было удалено")
        except (KeyError, ConfirmState.DoesNotExist):
            messages.error(request, "Эта ссылка уже не действительна")
        return HttpResponseRedirect(reverse("main"))


class GroupListView(JsonContextView):
    template_name = "groups/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = kwargs["group_user"].group
        today = get_today_for_user(self.request.user)
        pflist = group.get_prayforlist(date=today)
        context["group"] = group
        context["health"] = pflist["health"]
        context["rip"] = pflist["rip"]
        context["sick"] = pflist["sick"]
        context["war"] = pflist["war"]
        context["army"] = pflist["army"]
        context["pray"] = pflist["pray"]
        return context


class ReadingView(JsonContextView):
    template_name = "reading/group.html"

    @staticmethod
    def get_group(**kwargs):
        return kwargs["group_user"]

    def get_date(self, **kwargs):
        try:
            today = datetime.datetime.strptime(self.request.GET["d"],
                                               DATE_FORMAT).date()
        except (KeyError, ValueError):
            today = get_today_for_user(self.request.user)
        return today

    @staticmethod
    def get_date_url(group, date):
        return (reverse("reading") +
                "?g={}{}".format(group.link,
                                 "&d={}".format(date.strftime(DATE_FORMAT))
                                  if date else ""))

    @staticmethod
    def get_queue_url(group):
        return (reverse("reading-queue") +
                "?g={}".format(group.link))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_group(**kwargs)
        today = self.get_date(**kwargs)
        reading = group.get_reading(date=today)
        context["can_join"] = kwargs.get("can_join")
        context["name"] = group.name
        context["group"] = group
        context["starturl"] = self.get_date_url(group, group.settings.start)
        context["queueurl"] = self.get_queue_url(group)
        if reading is None:
            context["date"] = today
            context["bdate"] = group.settings.bdate
            return context
        context["date"] = reading["date"]
        context["data"] = reading["data"]
        context["prevdate"] = group.get_prevdate(today)
        context["nextdate"] = group.get_nextdate(today)
        context["prevurl"] = self.get_date_url(group, context["prevdate"])
        context["nexturl"] = self.get_date_url(group, context["nextdate"])
        context["reading"] = reading["reading"]
        context["health"] = reading["health"]
        context["rip"] = reading["rip"]
        context["sick"] = reading["sick"]
        context["war"] = reading["war"]
        context["army"] = reading["army"]
        context["pray"] = reading["pray"]
        return context


class GroupReadingView(ReadingView):

    @staticmethod
    def get_group(**kwargs):
        return kwargs["group_user"].group

    def get_date(self, **kwargs):
        try:
            today = datetime.date(year=kwargs["year"],
                                  month=kwargs["month"],
                                  day=kwargs["day"])
        except KeyError:
            today = get_today_for_user(self.request.user)
        return today

    @staticmethod
    def get_date_url(group, date):
        if date:
            return reverse("reading-group-date", kwargs={
                "id": group.id,
                "year": date.year,
                "month": date.month,
                "day": date.day,
            })
        return reverse("reading-group", kwargs={"id": group.id})

    @staticmethod
    def get_queue_url(group):
        return reverse("group-queue", kwargs={"id": group.id})


class QueueView(JsonContextView):
    template_name = "groups/queue.html"

    @staticmethod
    def get_group(**kwargs):
        return kwargs["group_user"]

    @staticmethod
    def get_date_url(group, date):
        return (reverse("reading") +
                "?g={}{}".format(group.link,
                                 "&d={}".format(date.strftime(DATE_FORMAT))
                                  if date else ""))

    def get_context_data(self, **kwargs):
        group = self.get_group(**kwargs)
        context = super().get_context_data(**kwargs)
        context["data"] = group.get_full_data
        settings = context["data"]["settings"]
        queue = list(context["data"]["volume"]["volume"].queue(
                                        step=settings.chpd))
        length = len(queue)
        idx = settings.start_idx - 1
        today = get_today_for_user(self.request.user)
        start = settings.start
        end = settings.end
        bstart = settings.break_start
        bend = settings.break_end

        if bstart:
            if bstart <= today <= bend:
                bstart = today
            break_days = (settings.bdate - bstart).days
        else:
            break_days = 0

        if today < start:
            dt = start
        elif end:
            if bstart is None:
                days = (end - start).days + 1
                if days < length:
                    dt = start
                    length = days
                else:
                    dt = end - datetime.timedelta(days=length-1)
                    idx += (dt - start).days
                    idx = idx % length
            else:
                dt = today
                if today > end:
                    if today < bend:
                        idx += (end - start).days + 1
                    else:
                        idx += (dt - start).days - break_days
                else:
                    idx += (dt - start).days
                idx = idx % length
        else:
            dt = today
            idx += (dt - start).days
            idx = idx % length

        lt = []
        i = 1
        delta_days = break_days if bstart and today <= bend else 0
        while i < length + delta_days + 1:
            if bstart and dt == bstart:
                j = 0
                while j < delta_days:
                    lt.append((i, dt, None, dt == today, None))
                    dt += DATE_DELTA_DAY
                    i += 1
                    j += 1
            try:
                qi = queue[idx]
            except IndexError:
                idx = 0
                qi = queue[idx]
            lt.append((i, dt, qi, dt == today,
                       self.get_date_url(group, dt)))
            i += 1
            idx += 1
            dt += DATE_DELTA_DAY
        context["queue"] = lt
        return context


class GroupQueueView(QueueView):

    @staticmethod
    def get_group(**kwargs):
        return kwargs["group_user"].group

    @staticmethod
    def get_date_url(group, date):
        if date:
            return reverse("reading-group-date", kwargs={
                "id": group.id,
                "year": date.year,
                "month": date.month,
                "day": date.day,
            })
        return reverse("reading-group", kwargs={"id": group.id})


class GroupCreateView(FormView):
    template_name = "groups/create.html"
    form_class = GroupCreateForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "form": GroupCreateForm()
        })

    def form_valid(self, form):
        if self.request.method != 'POST':
            return HttpResponseForbidden()

        settings = Settings.objects.create(start_idx=form.cleaned_data["start_idx"] or 1,
                                           chpd=form.cleaned_data["chpd"] or 1,
                                           names_cnt=form.cleaned_data["names_cnt"] or 0,
                                           start=form.cleaned_data["start"] or datetime.datetime.now(),
                                           end=form.cleaned_data["end"])
        cleaned_volume = form.cleaned_data["volume"] or -1
        if cleaned_volume > 0:
            volume_id = cleaned_volume
        elif cleaned_volume == 0:
            # Psaltir
            # check if volume exists
            try:
                vb = VolumeBook.objects.get(book__slug="psaltir-tserkovnoslavianskii")
                volume_id = vb.volume_id
            except VolumeBook.DoesNotExist:
                book = Book.objects.get(slug="psaltir-tserkovnoslavianskii")
                volume = Volume.objects.create(title="psaltir-tserkovnoslavianskii",
                                               creater_id=self.request.user.id,
                                               hidden=True)
                VolumeBook.objects.create(volume=volume, book_id=book.id)
                volume_id = volume.id
        else:
            # volume == -1,
            # creating from selected books
            book_ids = sorted(form.cleaned_data["book_id"])
            title = ", ".join(b.title for b in
                                Book.objects.filter(id__in=book_ids).order_by("id"))
            if len(title) > 255:
                title = title[:252] + "..."
            volume = Volume.objects.create(title=title,
                                           creater_id=self.request.user.id,
                                           hidden=True)
            vb = []
            for b in book_ids:
                vb.append(VolumeBook(volume=volume, book_id=b))
            VolumeBook.objects.bulk_create(vb)
            volume_id = volume.id

        while True:
            try:
                group = AgreementGroup.objects.create(name=form.cleaned_data["name"],
                                                      link=get_random_string(8),
                                                      settings=settings,
                                                      volume_id=volume_id)
                break
            except IntegrityError:
                pass
        agu = AgreementGroupUser.objects.create(group_id=group.id,
                                                user_id=self.request.user.id,
                                                role="A")
        # creating default root PrayForDiv for any list_type:
        pfd = PrayForDiv.objects.create(group=group, root=True)
        return HttpResponseRedirect(reverse("group", kwargs={"id": group.id}))


class GroupNewView(TemplateView):
    template_name = "groups/new.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["volume"] = None
        context["book"] = None
        context["name"] = ""
        try:
            context["volume"] = Volume.objects.get(id=int(self.request.GET["v"]))
            context["name"] = context["volume"].title[:100]
        except (KeyError, Volume.DoesNotExist, ValueError, TypeError):
            pass
        try:
            context["book"] = Book.objects.get(id=int(self.request.GET["b"]))
            context["name"] = context["book"].title
        except (KeyError, Book.DoesNotExist, ValueError, TypeError):
            pass
        return context


class GroupEditView(TemplateView):
    template_name = "groups/edit.html"

    def post(self, request, *args, **kwargs):
        agu = kwargs["group_user"]
        if not agu.perm_edit():
            return HttpResponseForbidden()

        group = agu.group
        ret = -1
        try:
            action = request.POST["action"]
            if action == "title":
                name = request.POST["name"]
                group.name = name
                group.save()
                ret = group.id
            elif action == "rem_member":
                (AgreementGroupUser.objects.filter(group_id=group.id,
                                                   user_id=request.user.id)
                                           .update(deleted=datetime.datetime.now()))
                return HttpResponseRedirect(reverse("main"))
            elif action == "startidx" and agu.perm_admin():
                num = int(request.POST["idx"])
                (Settings.objects.filter(id=group.settings_id)
                                 .update(start_idx=num))
            elif action == "chpd" and agu.perm_admin():
                num = int(request.POST["chpd"]) or 1
                (Settings.objects.filter(id=group.settings_id)
                                 .update(chpd=num))
            elif action == "namescnt" and agu.perm_admin():
                num = int(request.POST["cnt"]) or 0
                (Settings.objects.filter(id=group.settings_id)
                                 .update(names_cnt=num))
            elif action == "date" and agu.perm_admin():
                kw = {request.POST["name"]: request.POST["date"] or None}
                (Settings.objects.filter(id=group.settings_id)
                                 .update(**kw))
            elif action == "listorder" and agu.perm_admin():
                ch = request.POST["ch"]
                if ch not in ("A", "B"):
                    ch = "B"
                (Settings.objects.filter(id=group.settings_id)
                                 .update(listorder=ch))
            elif action == "rem_pray":
                (PrayGroup.objects
                          .filter(group_id=group.id, pray_id=request.POST["pray_id"])
                          .delete())
            elif action == "add_start_pray" or action == "add_end_pray":
                kw_key = "start" if action == "add_start_pray" else "end"
                kw = {"group_id": group.id}
                kw[kw_key] = True
                lt = []
                for _id in request.POST.getlist("pray_id[]"):
                    kw["pray_id"] = _id
                    lt.append(PrayGroup(**kw))
                PrayGroup.objects.bulk_create(lt)
            elif action == "sort_start_pray" or action == "sort_end_pray":
                seria = request.POST["seria"].split(",")
                kw_key = "start" if action == "add_start_pray" else "end"
                kw = {"group_id": group.id}
                kw[kw_key] = True
                prays = [p for p in PrayGroup.objects.filter(**kw).order_by("order")]
                sort_querylist(prays, seria)
            elif action == "add_div":
                p = PrayForDiv.objects.create(group_id=group.id,
                                              order=request.POST["order"])
                pf = PrayFor.objects.create(div_id=p.id, name="",
                                            list_type=request.POST["list"])
                ret = {"div": p.id, "pf": pf.id}
            elif action == "del_div":
                div_id = request.POST["div_id"]
                PrayFor.objects.filter(div_id=div_id).delete()
                PrayForDiv.objects.filter(id=div_id).delete()
            elif action == "sort_div":
                seria = request.POST["seria"].split(",")
                lt = [p for p in PrayFor.objects.filter(div_id=request.POST["div_id"],
                                                        list_type=request.POST["list"],
                                                        deleted=False).order_by("order", "id")]
                sort_querylist(lt, seria)
            elif action == "div_name":
                div_id = request.POST["div_id"]
                PrayForDiv.objects.filter(id=div_id).update(name=request.POST["name"])
                ret = div_id
            elif action == "prayfor_name":
                pf_id = request.POST["pf_id"]
                PrayFor.objects.filter(id=pf_id).update(name=request.POST["name"])
                ret = pf_id
            elif action == "prayfor_till":
                pf_id = request.POST["pf_id"]
                PrayFor.objects.filter(id=pf_id).update(till=request.POST["till"] or None)
                ret = pf_id
            elif action == "add_prayfor":
                p = PrayFor.objects.create(div_id=request.POST["div_id"], name="",
                                           list_type=request.POST["list"],
                                           order=request.POST["order"])
                ret = p.id
            elif action == "rem_prayfor":
                PrayFor.objects.filter(id=request.POST["pf_id"]).delete()
            elif action == "change_role":
                if not agu.perm_admin():
                    return HttpResponseForbidden()
                role = request.POST["role"]
                if role in [r[0] for r in ROLES]:
                    (AgreementGroupUser.objects.filter(user_id=request.POST["uid"])
                                               .update(role=role))
            else:
                raise ValueError
        except (KeyError, ValueError, IntegrityError):
            return JsonResponse({"error": ret})
        History.objects.create(user_id=request.user.id, group_id=group.id,
                               action=action)
        return JsonResponse({"ok": ret})


def add_to_group(request):
    user_id = request.user.id
    if request.method == "POST":
        try:
            pk = request.POST["id"]
            try:
                agu = AgreementGroupUser.objects.get(group_id=pk,
                                                     user_id=user_id)
                if agu.deleted:
                    agu.deleted = None
                    agu.save(update_fields=["deleted"])
            except AgreementGroupUser.DoesNotExist:
                AgreementGroupUser.objects.create(group_id=pk,
                                                  user_id=user_id)
            return HttpResponseRedirect(reverse("group", kwargs={"id": pk}))
        except KeyError:
            pass
    return HttpResponseForbidden()

