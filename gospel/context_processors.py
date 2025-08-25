
from gospel.models import (AgreementGroupUser, Counter, get_today_for_user,
                           DATE_FORMAT)
from gospel.json import is_json


def groups(request):
    return {
        "groups": (AgreementGroupUser.objects
                                     .select_related("group",
                                                     "group__settings")
                                     .filter(user_id=request.user.id,
                                             deleted=None)
                                     .order_by("-group__settings__bdate",
                                               "group__settings__end",
                                               "group__settings__start")),
    }


def counter(request):
    counter = 0
    if not is_json(request):
        path = request.get_full_path()
        try:
            counter = Counter.objects.get(path=path).count
        except Counter.DoesNotExist:
            pass
    return {
        "counter": counter
    }

def user_today_date(request):
    return {
        "user_today_date": get_today_for_user(request.user).strftime(DATE_FORMAT)
    }
