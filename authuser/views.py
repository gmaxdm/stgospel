#coding=utf-8
import logging
import ujson
import datetime

from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from django.views import View
from django.views.generic.edit import CreateView, FormView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin

from authuser.models import (User, ConfirmState, Feedback, Prayers,
                             Synodik, sort_querylist)
from authuser.forms import NewUserForm, PasswordForm, RemindForm

from gospel.json import (JsonContextView, JsonFileView)


logger = logging.getLogger("django")


class LoginRequired(LoginRequiredMixin):
    login_url = settings.LOGIN_URL


class EmailBlacklist:

    @classmethod
    def blacklist(cls):
        if not hasattr(cls, "_bl"):
            cls._bl = set()
            with open(settings.EMAIL_BLACKLIST_FILE) as f:
                for line in f:
                    cls._bl.add(line.strip())
        return cls._bl

    @classmethod
    def userlist(cls):
        if not hasattr(cls, "_ubl"):
            cls._ubl = set()
            with open(settings.USER_BLACKLIST_FILE) as f:
                for line in f:
                    cls._ubl.add(line.strip())
        return cls._ubl

    @classmethod
    def is_ban(cls, email):
        if email in cls.blacklist():
            return True
        try:
            username = email.split("@")[0]
        except IndexError:
            return True

        username = username.replace(".", "")
        if username in cls.userlist():
            return True

        return False


def send_mail(to, subject, template, context=None):
    if EmailBlacklist.is_ban(to.strip()):
        logger.info("email {} is banned".format(to))
        return

    letter = render_to_string(template, context)
    mes = EmailMessage(subject=subject, body=letter, to=[to])
    mes.content_subtype = "html"
    try:
        mes.send()
        logger.info("sent email to {}".format(to))
    except:
        logger.error("Can't send email to {}".format(to))
        raise


class RegisterView(CreateView):
    model = User
    form_class = NewUserForm
    template_name = "forms/register.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": NewUserForm()
        })

    def form_valid(self, form):
        if self.request.method == 'POST':
            email = form.cleaned_data['email']
            if email.strip() in EmailBlacklist.blacklist():
                messages.error(self.request, f"{email} is blacklisted")
                return HttpResponseRedirect(reverse("register"))
            try:
                user = User.objects.get(username=email, email=email)
                messages.error(self.request,
                               "Пользователь с таким email уже зарегистрирован в системе")
            except User.DoesNotExist:
                data = ujson.dumps(form.cleaned_data)
                confirmstr = get_random_string(32)
                ConfirmState(confirmstr=confirmstr, data=data).save()
                letter = render_to_string('letters/confirm_letter.html',
                                          {
                                              'first_name': form.cleaned_data['first_name'],
                                              'last_name': form.cleaned_data['last_name'],
                                              'confirmstr': confirmstr
                                          })
                mes = EmailMessage(subject="Регистрация на st-gospel.ru",
                                   body=letter, to=[email])
                mes.content_subtype = "html"
                try:
                    mes.send()
                    messages.success(self.request,
                                     "Вам выслано письмо с информацией для завершения регистрации")
                except:
                    messages.error(self.request,
                                   "Не удается выслать письмо на указанный адрес")
                    logger.error("Can't send email to {}".format(email))
            return HttpResponseRedirect(reverse("register"))


class RemindView(FormView):
    form_class = RemindForm
    template_name = "forms/remind.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": RemindForm()
        })

    def form_valid(self, form):
        if self.request.method == 'POST':
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(username=email, email=email)
                data = ujson.dumps(form.cleaned_data)
                confirmstr = get_random_string(32)
                ConfirmState(confirmstr=confirmstr, data=data, remind=True).save()
                letter = render_to_string('letters/remind_letter.html',
                                          {
                                              'first_name': user.first_name,
                                              'last_name': user.last_name,
                                              'confirmstr': confirmstr
                                          })
                mes = EmailMessage(subject="Восстановление пароля на st-gospel.ru",
                                   body=letter, to=[email])
                mes.content_subtype = "html"
                try:
                    mes.send()
                    messages.success(self.request,
                                     "Вам выслано письмо с информацией для "
                                     "завершения восстановления пароля")
                except:
                    messages.error(self.request,
                                   "Не удается выслать письмо на указанный адрес")
                    logger.error("Can't send email to {}".format(email))
            except User.DoesNotExist:
                messages.error(self.request,
                               "Пользователя с таким email в системе не существует")
            return HttpResponseRedirect(reverse("remind"))


class RegisterConfirmView(View):

    @never_cache
    def get(self, request):
        try:
            confirmstr = request.GET['t']
            state = ConfirmState.objects.get(confirmstr=confirmstr)
            data = ujson.loads(state.data)
            state.delete()
            try:
                user = User.objects.get(username=data["email"], email=data['email'])
                messages.error(request, "Пользователь с таким email уже зарегистрирован в системе")
            except User.DoesNotExist:
                user = User.objects.create_user(data['email'],
                                                email=data['email'],
                                                password=data['password2'],
                                                first_name=data['first_name'],
                                                last_name=data['last_name'])
                auth_login(request, user)
                messages.success(request, "Вы успешно зарегистрировались на сайте!")
                return HttpResponseRedirect(reverse("main"))
        except (KeyError, ConfirmState.DoesNotExist):
            messages.error(request, "У вас недостаточно прав для совершения этого действия")
        return HttpResponseRedirect(reverse("register"))


class RemindConfirmView(View):

    @never_cache
    def get(self, request):
        try:
            confirmstr = request.GET['t']
            state = ConfirmState.objects.get(confirmstr=confirmstr)
            data = ujson.loads(state.data)
            state.delete()
            try:
                user = User.objects.get(username=data['email'], email=data["email"])
                user.new_passwd = get_random_string(7)
                user.set_password(user.new_passwd)
                user.save()
                auth_login(request, user)
                letter = render_to_string('letters/passwd_letter.html',
                                          {
                                              'first_name': user.first_name,
                                              'last_name': user.last_name,
                                              'password': user.new_passwd,
                                          })
                mes = EmailMessage(subject="Восстановление пароля на st-gospel.ru",
                                   body=letter, to=[user.email])
                mes.content_subtype = "html"
                try:
                    mes.send()
                    messages.success(request,
                                     "Новый пароль выслан вам на электронную почту. "
                                     "При желании вы можете изменить его в Профиле")
                except:
                    messages.error(request,
                                   "Не удается выслать письмо на указанный адрес")
                    logger.error("Can't send email to {}".format(email))
                return HttpResponseRedirect(reverse("main"))
            except User.DoesNotExist:
                messages.error(request, "Пользователя с таким email в системе не существует")
        except (KeyError, ConfirmState.DoesNotExist):
            messages.error(request, "У вас недостаточно прав для совершения этого действия")
        return HttpResponseRedirect(reverse("main"))


class ProfileView(LoginRequired, TemplateView):
    template_name = "profile.html"

    def post(self, request):
        modified = False
        name = request.POST["name"]
        if request.user.first_name != name:
            request.user.first_name = name
            modified = True
        surname = request.POST["surname"]
        if request.user.last_name != surname:
            request.user.last_name = surname
            modified = True
        notify = 1 if request.POST.get("notify") else 0
        if request.user.notify != notify:
            request.user.notify = notify
            modified = True
        tz_city = request.POST["tz_city"]
        if request.user.tz_city != tz_city:
            request.user.tz_city = tz_city
            modified = True
        time_zone = request.POST["time_zone"]
        if request.user.time_zone != time_zone:
            request.user.time_zone = time_zone
            modified = True
        p1 = request.POST["password1"]
        p2 = request.POST["password2"]
        if p1 and p2:
            form = PasswordForm(request.POST)
            if not form.is_valid():
                if modified:
                    request.user.save()
                return render(request, self.template_name, {
                    "form": form,
                })
            request.user.set_password(form.cleaned_data["password2"])
            modified = True
            messages.success(request,
                             "Ваш пароль успешно изменен")
        if modified:
            request.user.save()
        return HttpResponseRedirect(reverse("profile"))


class FeedbackView(LoginRequired, TemplateView):
    template_name = "feedback.html"

    def post(self, request):
        msg = request.POST['msg']
        if msg:
            try:
                ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0]
            except KeyError:
                ip = request.META['REMOTE_ADDR']
            Feedback.objects.create(user_id=request.user.id, ip=ip, msg=msg)
            messages.success(request, "Благодарим вас за обратную связь!")
        return HttpResponseRedirect(reverse("feedback"))


class CitiesView(LoginRequired, JsonFileView):
    def get_filedata(self, request, *args, **kwargs):
        with open(settings.CITIES_FILTER_FILE) as f:
            data = f.read()
        return data


class MyPrayListView(LoginRequired, JsonContextView):
    template_name = "myprayers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prayers"] = (Prayers.objects.select_related("pray")
                                     .filter(user=self.request.user.id))
        return context


class MyPrayersEditView(LoginRequired, TemplateView):
    template_name = "myprayers_edit.html"

    def post(self, request, *args, **kwargs):
        ret = -1
        try:
            action = request.POST["action"]
            if action == "rem_pray":
                (Prayers.objects
                        .filter(user_id=request.user.id, pray_id=request.POST["pray_id"])
                        .delete())
            elif action == "add_pray":
                lt = []
                for _id in request.POST.getlist("pray_id[]"):
                    lt.append(Prayers(user_id=request.user.id, pray_id=_id))
                Prayers.objects.bulk_create(lt)
            ret = 1
        except KeyError:
            return JsonResponse({"error": ret})
        return JsonResponse({"ok": ret})


class MySynodikBaseView(JsonContextView):
    template_name = "synodik/synodik.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            return context

        context["synodik"] = (Synodik.objects
                                     .filter(user_id=self.request.user.id,
                                             deleted=False)
                                     .order_by('order', 'id'))
        today = datetime.datetime.now().date()
        # TODO: render synodik lists by React
        hnames = []
        rnames = []
        snames = []
        wnames = []
        anames = []
        for n in context["synodik"]:
            _type = n.list_type
            if _type == "H":
                names = hnames
            elif _type == "R":
                names = rnames
            elif _type == "W":
                names = wnames
            elif _type == "S":
                names = snames
            elif _type == "A":
                names = anames
            else:
                continue

            if (not n.name or
                (n.till and today > n.till)):
                continue

            names.append({
                "id": n.id,
                "name": n.name,
                "till": n.till,
            })
        context.update({
            "date": today,
            "health": hnames,
            "rip": rnames,
            "sick": snames,
            "war": wnames,
            "army": anames,
        })
        context["root"] = {
            "id": self.request.user.id,
            "name": str(self.request.user),
        }
        return context


class MySynodikView(LoginRequired, MySynodikBaseView):
    template_name = "synodik/synodik.html"


class MySynodikEditView(LoginRequired, TemplateView):
    template_name = "synodik/edit.html"

    def post(self, request, *args, **kwargs):
        ret = -1
        try:
            action = request.POST["action"]
            if action == "sort_div":
                seria = request.POST["seria"].split(",")
                lt = [p for p in Synodik.objects.filter(user_id=request.user.id,
                                                        list_type=request.POST["list"],
                                                        deleted=False).order_by("order", "id")]
                sort_querylist(lt, seria)
            elif action == "prayfor_name":
                pf_id = request.POST["pf_id"]
                Synodik.objects.filter(id=pf_id).update(name=request.POST["name"])
                ret = pf_id
            elif action == "prayfor_till":
                pf_id = request.POST["pf_id"]
                Synodik.objects.filter(id=pf_id).update(till=request.POST["till"] or None)
                ret = pf_id
            elif action == "add_prayfor":
                p = Synodik.objects.create(user_id=request.user.id, name="",
                                           list_type=request.POST["list"],
                                           order=request.POST["order"])
                ret = p.id
            elif action == "rem_prayfor":
                Synodik.objects.filter(id=request.POST["pf_id"]).delete()
            else:
                raise ValueError
        except (KeyError, ValueError, IntegrityError) as e:
            return JsonResponse({"error": str(e)})
        return JsonResponse({"ok": ret})

