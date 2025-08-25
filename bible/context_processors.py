from bible.models import Volume


def volumes(request):
    return {
        "volumes": Volume.objects.filter(public=True,
                                         hidden=False),
    }

