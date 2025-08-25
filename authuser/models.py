#coding=utf-8
import re

from django.db import models
from django.contrib.auth.models import AbstractUser


RE_EMAIL = re.compile(r"(\w+)\s+((\w+)\s+)?<(.+)>", re.IGNORECASE)

LIST_TYPES = (
    ("H", "О здравии"),
    ("R", "О упокоении"),
    ("S", "О болящих"),
    ("W", "О враждующих"),
    ("A", "О воинах"),
)


class User(AbstractUser):
    bdate = models.DateField("Дата рождения", null=True, blank=True)
    notify = models.PositiveSmallIntegerField(default=1)
    invite = models.DateField("Дата приглашения", null=True, auto_now_add=True)
    posts = models.PositiveIntegerField(default=0)
    locale = models.CharField("Язык", max_length=2, default='ru')
    tz_city = models.CharField("Город из часового пояса", max_length=100, default="Москва")
    time_zone = models.CharField("Часовой пояс", max_length=100, default="Europe/Moscow")

    def __str__(self):
        if self.first_name or self.last_name:
            return "{} {}".format(self.first_name, self.last_name)
        return self.username


class ConfirmState(models.Model):
    confirmstr = models.CharField("Строка подтверждения", unique=True, max_length=128)
    data = models.TextField("Данные о пользователе")
    remind = models.BooleanField("Пароль", default=False)
    invite = models.BooleanField("Приглашение", default=False)
    cdate = models.DateTimeField("Дата создания", auto_now=True)


class Feedback(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    ip = models.CharField(max_length=15)
    msg = models.TextField()
    cdate = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return "{} ({}) от {}".format(self.msg[:79], self.user, self.cdate.date())


class Prayers(models.Model):
    user = models.ForeignKey(User, models.CASCADE)
    pray = models.ForeignKey("bible.Pray", models.CASCADE)
    cdate = models.DateTimeField("Дата добавления", auto_now=True)

    def to_json(self):
        return self.pray.to_json()


def sort_querylist(querylist, seria):
    update_fields = ["order"]
    for i, pr in enumerate(seria):
        idx = int(pr) - 1
        it = querylist[idx]
        n = i + 1
        if it.order != n:
            it.order = n
            it.save(update_fields=update_fields)


def get_names(values, group_by):
    names = []
    lt = []
    i = 0
    for div in sorted(values, key=lambda x: x["order"]):
        if not div["list"]:
            continue
        lt.append(div)
        i += 1
        if i == group_by:
            names.append(lt)
            i = 0
            lt = []
    if lt:
        names.append(lt)
    return names


class PrayForAbstract(models.Model):
    name = models.CharField("Имя нуждающегося", max_length=100)
    list_type = models.CharField("Тип списка", max_length=1, choices=LIST_TYPES)
    till = models.DateField("Поминать до", null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "list": self.list_type,
            "till": self.till,
            "order": self.order,
        }


class Synodik(PrayForAbstract):
    user = models.ForeignKey(User, models.CASCADE)

