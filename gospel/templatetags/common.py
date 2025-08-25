# coding=utf-8
from datetime import datetime, date
from django import template
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from gospel.models import word_declension, DATE_FORMAT, get_today_for_user


register = template.Library()


def _as_date(value):
    return datetime.strptime(value, DATE_FORMAT).date()


@register.filter
def declension(value, word):
    words = list(map(_, word.split(',')))
    return words[word_declension(value)]


@register.filter
def calendar(value):
    if isinstance(value, date):
        dt = value
    elif isinstance(value, datetime):
        dt = value.date()
    elif isinstance(value, str):
        try:
            dt = _as_date(value)
        except ValueError:
            dt = datetime.now().date()
    return mark_safe('<a class="text-nowrap" href="/calendar/{}/">{}</a>'
                     .format("/".join(map(str, [dt.year, dt.month, dt.day])),
                             formats.date_format(dt, format="DATE_FORMAT")))


@register.filter
def as_date(value):
    return _as_date(value)


@register.filter
def today(user):
    return get_today_for_user(user)


@register.simple_tag(takes_context=True)
def group_date(context, group, days):
    user = context['user']
    today = get_today_for_user(user)
    return group.get_date(today, days=days)


@register.simple_tag(takes_context=True)
def is_group_finished(context, group, date=None):
    if date is None:
        user = context['user']
        date = get_today_for_user(user)
    return group.is_finished(date)


@register.filter
def mongo_id(value):
    return str(value["_id"])

