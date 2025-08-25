# coding=utf-8
import os
import datetime
import ujson

from django.db import models
from django.conf import settings

from authuser.models import User, PrayForAbstract, get_names
from bible.models import Volume, Pray, Line
from timezone_converter import TimezoneConverter


ROLES = (
    ("A", "Администратор"),
    ("E", "Редактор"),
    ("U", "Участник"),
)

HISTORY_ACTIONS = (
    ("new_member", "новый пользователь добавился в группу"),
    ("rem_member", "пользователь покинул группу"),
    ("title", "изменено названия группы"),
    ("startidx", "изменена начальная глава чтения"),
    ("chpd", "изменено количество глав чтения в день"),
    ("namescnt", "изменено максимальное количество имен в списке"),
    ("date", "изменена дата чтения"),
    ("rem_pray", "удалена молитва из группы"),
    ("add_start_pray", "добавлена молитва в начало"),
    ("add_end_pray", "добавлена молитва в конец"),
    ("sort_start_pray", "изменен порядок молитв в начале"),
    ("sort_end_pray", "изменен порядок молитв в конце"),
    ("add_div", "добавлен новый список с именами"),
    ("del_div", "удален список с именами"),
    ("sort_div", "изменен порядок в списке с именами"),
    ("div_name", "изменено имя списка с именами"),
    ("prayfor_name", "изменено имя в списке"),
    ("prayfor_till", "изменена дата окончания для имени в списке"),
    ("add_prayfor", "добавлено имя в список"),
    ("rem_prayfor", "удалено имя из списка"),
    ("change_role", "изменена роль участника"),
    ("listorder", "изменен порядок следования списков поминовения при чтении"),
)


LIST_ORDER = (
    ("A", "после всех глав"),
    ("B", "между главами"),
)


TRAPEZA_ID = {
    "Поста нет.": 1,
    "Монастырский устав: cухоядение (хлеб, овощи, фрукты).": 2,
    "Разрешается рыба.": 3,
    "Из трапезы исключается мясо.": 4,
    "По монастырскому уставу - полное воздержание от пищи.": 5,
    "Пища с растительным маслом.": 6,
    "Разрешается рыбная икра.": 7,
    "Монастырский устав: горячая пища без масла.": 8,
}


DATE_FORMAT = "%Y-%m-%d"

DATE_DELTA_DAY = datetime.timedelta(days=1)
DATE_DELTA_DAY_13 = datetime.timedelta(days=13)


def word_declension(num):
    if 0 < num < 1:
        return 2
    if num > 100:
        num %= 100
    if 10 < num < 15:
        return 2
    else:
        num %= 10
        if num == 0 or 5 <= num <= 9:
            return 2
        elif num == 1:
            return 0
        elif 2 <= num <= 4:
            return 1


def get_today(user_tz_name=None, with_time=False):
    now = datetime.datetime.now()
    if user_tz_name is not None and user_tz_name != settings.TIME_ZONE:
        conv = TimezoneConverter()
        now = conv.from_to(now, settings.TIME_ZONE, user_tz_name)
    return now if with_time else now.date()


def get_today_for_user(user, with_time=False):
    return get_today(user_tz_name=user.time_zone
                        if user.is_authenticated else None,
                     with_time=with_time)


class OrthodoxCalendar:

    def __init__(self, date=None, tz_name=None):
        if date is None or isinstance(date, datetime.date):
            self.date = date or get_today(user_tz_name=tz_name)
        else:
            self.date = datetime.datetime.strptime(date, DATE_FORMAT)

    @staticmethod
    def __get_filename(date):
        dt = date.strftime(DATE_FORMAT)
        return "{}.json".format(dt)

    @staticmethod
    def __read_data(filename):
        # here year dir is got as filename[:4]
        try:
            with open(os.path.join(settings.BASE_DIR, "gospel", "calendar",
                                   filename[:4], "json",
                                   filename)) as f:
                return ujson.loads(f.read())
        except (FileNotFoundError, ValueError):
            return {}

    @staticmethod
    def all():
        """ return generator of dicts
        """
        for filename in sorted(os.listdir(settings.CALENDAR_YEAR_DIR)):
            yield OrthodoxCalendar.__read_data(filename)

    @property
    def filename(self):
        if not hasattr(self, "_filename"):
            self._filename = self.__get_filename(self.date)
        return self._filename

    @property
    def data(self):
        if not hasattr(self, "_data"):
            self._data = self.__read_data(self.__get_filename(self.date))
        return self._data

    def find_next_holiday(self):
        i = 0
        dt = self.date + DATE_DELTA_DAY
        while True:
            data = self.__read_data(self.__get_filename(dt))
            if not data or data["title"]:
                break
            dt += DATE_DELTA_DAY
            i += 1
        if data:
            return {
                "days": i,
                "data": data,
                "date": dt,
            }
        return None


class Settings(models.Model):
    """How to set break date:
    Break date range is set by:
    - end date + 1 day
    - bdate as an end date of break period.
    bdate should be greater then end
    """
    start_idx = models.PositiveSmallIntegerField("Начальный индекс последовательности", default=1)
    chpd = models.PositiveSmallIntegerField("Количество глав в день", default=1)
    names_cnt = models.PositiveSmallIntegerField("Количество имен в списке", default=0)
    start = models.DateField("Дата начала чтения")
    end = models.DateField("Дата завершения", null=True, blank=True)
    bdate = models.DateField("Дата возобновления чтения", null=True, blank=True)
    listorder = models.CharField(max_length=1, choices=LIST_ORDER, default="B")

    def __str__(self):
        return self.start.strftime(DATE_FORMAT)

    def is_break_date(self):
        return self.bdate and self.end and self.bdate > self.end + DATE_DELTA_DAY

    @property
    def break_start(self):
        if self.is_break_date():
            return self.end + DATE_DELTA_DAY
        return None

    @property
    def break_end(self):
        if self.is_break_date():
            return self.bdate - DATE_DELTA_DAY
        return None

    def get_queue_index(self, dt, length):
        idx = self.start_idx - 1
        idx += (dt - self.start).days
        return idx % length

    def to_json(self):
        return {
            "id": self.id,
            "start_idx": self.start_idx,
            "chpd": self.chpd,
            "ncnt": self.names_cnt,
            "start": self.start,
            "end": self.end,
            "bdate": self.bdate,
            "lorder": self.listorder,
        }


class AgreementGroup(models.Model):
    name = models.CharField("Название чтения (группы)", max_length=100)
    link = models.CharField("Внешняя ссылка", max_length=8, unique=True)
    public = models.BooleanField(default=False)
    volume = models.ForeignKey(Volume, models.CASCADE)
    settings = models.ForeignKey(Settings, models.CASCADE)
    users = models.ManyToManyField(User, through='AgreementGroupUser')
    prays = models.ManyToManyField(Pray, through='PrayGroup')
    mdate = models.DateTimeField("Дата изменения", auto_now=True)
    cdate = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Чтение"
        verbose_name_plural = "Чтения"

    def __str__(self):
        return self.name

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "link": self.link,
            "volume_id": self.volume_id,
            "settings_id": self.settings_id,
        }

    @property
    def get_full_data(self):
        if not hasattr(self, "_fulldata"):
            self._fulldata = {
                "group": self,
                "volume": Volume.objects.get(id=self.volume_id).get_full_data,
                "settings": self.settings,
                "prays": (PrayGroup.objects.select_related("pray")
                                           .filter(group_id=self.id)
                                           .order_by("order")),
                "list": (PrayForDiv.objects
                                   .filter(group_id=self.id)
                                   .values("id", "name", "order",
                                           "root",
                                           "prayfor__id",
                                           "prayfor__name",
                                           "prayfor__list_type",
                                           "prayfor__till",
                                           "prayfor__order")
                                   .order_by("prayfor__order",
                                             "prayfor__id")),
            }
        return self._fulldata

    def get_date(self, date, days=0):
        if days:
            date = date + datetime.timedelta(days=days)
        data = self.get_full_data
        settings = data["settings"]
        end = settings.end
        return date if (date >= settings.start and
                        (not end or date <= end or
                         (settings.is_break_date() and
                          settings.bdate <= date))) else None

    def is_finished(self, date):
        return self.settings.end and date > self.settings.end

    def get_prevdate(self, date):
        return self.get_date(date, days=-1)

    def get_prevprevdate(self, date):
        return self.get_date(date, days=-2)

    def get_nextdate(self, date):
        return self.get_date(date, days=1)

    def get_prayforlist(self, date=None, group_by=2):
        if date is None:
            return

        data = self.get_full_data
        hnames = {}
        rnames = {}
        snames = {}
        wnames = {}
        pnames = {}
        anames = {}
        for div in data["list"]:
            _type = div["prayfor__list_type"]
            if _type == "H":
                names = hnames
            elif _type == "R":
                names = rnames
            elif _type == "W":
                names = wnames
            elif _type == "P":
                names = pnames
            elif _type == "S":
                names = snames
            elif _type == "A":
                names = anames
            else:
                continue

            try:
                n = names[div["id"]]
            except KeyError:
                n = names[div["id"]] = {
                    "id": div["id"],
                    "name": div["name"],
                    "order": div["order"],
                    "list": [],
                }
            if (not div["prayfor__name"] or
                (div["prayfor__till"] and date > div["prayfor__till"])):
                continue
            n["list"].append({
                "id": div["prayfor__id"],
                "name": div["prayfor__name"],
                "till": div["prayfor__till"],
            })
        return {
            "health": get_names(hnames.values(), group_by),
            "rip": get_names(rnames.values(), group_by),
            "sick": get_names(snames.values(), group_by),
            "war": get_names(wnames.values(), group_by),
            "army": get_names(anames.values(), group_by),
            "pray": get_names(pnames.values(), group_by),
        }

    def get_reading(self, date=None):
        cdate = self.get_date(date)
        if cdate is None:
            return

        data = self.get_full_data
        settings = data["settings"]
        start_idx = settings.start_idx - 1
        start = settings.start
        delta = cdate - start
        idx = start_idx + delta.days
        bend = settings.break_end
        if bend and cdate > bend:
            idx -= (bend - settings.end).days
        reading = data["volume"]["volume"].get_reading(
                                    idx=idx,
                                    step=settings.chpd)
        prayforlist = self.get_prayforlist(date=cdate)
        return {
            "data": data,
            "reading": reading,
            "health": prayforlist["health"],
            "rip": prayforlist["rip"],
            "sick": prayforlist["sick"],
            "war": prayforlist["war"],
            "pray": prayforlist["pray"],
            "army": prayforlist["army"],
            "date": cdate,
            "name": cdate.strftime(DATE_FORMAT),
        }


class AgreementGroupUser(models.Model):
    group = models.ForeignKey(AgreementGroup, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)
    settings = models.ForeignKey(Settings, models.SET_NULL, null=True, blank=True)
    role = models.CharField("Роль", default="U", max_length=1, choices=ROLES)
    joined = models.DateField("Дата присоединения", auto_now_add=True)
    deleted = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("group", "user")

    def to_json(self):
        return {
            "edit": self.perm_edit(),
            "admin": self.perm_admin(),
            "group_id": self.group_id,
            "user_id": self.user_id,
        }

    def perm_admin(self):
        return self.role == "A"

    def perm_edit(self):
        return self.perm_admin() or self.role == "E"


class PrayForDiv(models.Model):
    owner = models.ForeignKey(User, models.SET_NULL, null=True, blank=True)
    group = models.ForeignKey(AgreementGroup, models.CASCADE)
    name = models.CharField("Имя молящегося", max_length=200, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    root = models.BooleanField(default=False)


class PrayFor(PrayForAbstract):
    div = models.ForeignKey(PrayForDiv, models.CASCADE)

    def to_json(self):
        res = super().to_json()
        res.update({
            "div": {
                "id": self.div.id,
                "name": self.div.name,
                "order": self.div.order,
            }
        })
        return res


class PrayGroup(models.Model):
    pray = models.ForeignKey(Pray, models.CASCADE)
    group = models.ForeignKey(AgreementGroup, models.CASCADE)
    start = models.BooleanField("В начале", default=False)
    end = models.BooleanField("В конце", default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("pray", "group")

    def to_json(self):
        res = self.pray.to_json()
        res["start"] = self.start
        res["end"] = self.end
        res["order"] = self.order
        return res


class History(models.Model):
    user = models.ForeignKey(User, models.SET_NULL, null=True, blank=True)
    group = models.ForeignKey(AgreementGroup, models.CASCADE)
    action = models.CharField(max_length=30, choices=HISTORY_ACTIONS)
    text = models.CharField(max_length=100)
    cdate = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_action_display()

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "cdate": self.cdate,
        }


class Counter(models.Model):
    path = models.CharField(max_length=200, db_index=True)
    count = models.PositiveIntegerField()

