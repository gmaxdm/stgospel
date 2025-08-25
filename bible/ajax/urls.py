from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page

from bible.views import (BibleView, VolumeListView, VolumeEditView, BookView,
                         ChapterView, VolumeView)


HOURLY = 60*60


urlpatterns = [
    #path('', cache_page(HOURLY)(BibleView.as_view()), name="j-bible"),
    path('', BibleView.as_view(), name="j-bible"),
    path('book/<int:id>/', BookView.as_view(), name="j-book"),
    path('book/<int:id>/chapter/<int:num>/', ChapterView.as_view(), name="j-chapter"),
    path('volume/<int:id>/', VolumeView.as_view(), name="j-volume"),
    path('volume/', VolumeListView.as_view(), name="j-volumes"),
    path('volume/edit/', csrf_protect(VolumeEditView.as_view()), name="j-volume-edit")
]

