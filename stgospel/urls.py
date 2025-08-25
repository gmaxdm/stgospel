"""stgospel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page

from authuser.views import (RegisterView, RemindView, RegisterConfirmView,
                            RemindConfirmView, ProfileView, FeedbackView,
                            MyPrayListView, MyPrayersEditView, MySynodikView,
                            MySynodikEditView, CitiesView)
from gospel.views import (main, group_access, group_exist, GroupView, GroupCreateView,
                          GroupEditView, GroupReadingView, GroupQueueView, ReadingView,
                          GroupInviteView, GroupMembersView, InviteConfirmView,
                          CalendarView, GroupListView, CalendarShiftView, QueueView,
                          TroparionView, GroupNewView, add_to_group, CalendarMonthView)
from bible.views import (BibleView, BookView, ChapterView, ChapterVolumeView,
                         VolumeCreateView, VolumeEditView, VolumeRemoveView,
                         VolumeListView, VolumeView, VolumeQueueView,
                         PrayView, PrayListView, LinesView, MyVolumeListView,
                         TroparView, CommunionView, MorningView, KanonAveMariaView,
                         PsalterView)
from search.views import SearchView
from epub.views import EPubView


HOURLY = 60*60


urlpatterns = [
    path('', main, name="main"),
    path('about/', TemplateView.as_view(template_name="about.html"), name="about"),
    path('feedback/', csrf_protect(FeedbackView.as_view()), name="feedback"),
    #path('cities/', cache_page(60 * 60 * 24 * 7)(CitiesView.as_view()), name="cities"),
    path('cities/', CitiesView.as_view(), name="cities"),

    path('login/', auth_views.LoginView.as_view(template_name="login.html"),
         name="login"),
    path('register/', RegisterView.as_view(), name="register"),
    path('register/confirm/', RegisterConfirmView.as_view(), name="register-confirm"),
    path('remind/', RemindView.as_view(), name="remind"),
    path('remind/confirm/', RemindConfirmView.as_view(), name="remind-confirm"),
    path('logout/', auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path('profile/', csrf_protect(ProfileView.as_view()), name="profile"),
    path('profile/prayers/', csrf_protect(MyPrayListView.as_view()), name="myprayers"),
    path('profile/prayers/edit/', csrf_protect(MyPrayersEditView.as_view()),
         name="myprayers-edit"),
    path('profile/prayers/ajax/edit/', csrf_protect(MyPrayersEditView.as_view()),
         name="j-myprayers-edit"),
    path('profile/synodik/', MySynodikView.as_view(), name="mysynodik"),
    path('profile/synodik/edit/', csrf_protect(MySynodikEditView.as_view()),
         name="mysynodik-edit"),
    path('profile/synodik/ajax/', MySynodikView.as_view(),
         name="j-synodik"),
    path('profile/synodik/ajax/edit/', csrf_protect(
                                       MySynodikEditView.as_view()),
         name="j-synodik-edit"),
    path('calendar/<int:year>/<int:month>/<int:day>/', CalendarView.as_view(), name="calendar"),
    path('calendar/ajax/<int:year>/<int:month>/<int:day>/',
         CalendarView.as_view(), name="j-calendar"),
    path('calendar/shift/ajax/forward/<int:days>/',
         CalendarShiftView.as_view(), name="j-calendar-shift-forward"),
    path('calendar/shift/ajax/backward/<int:days>/',
         CalendarShiftView.as_view(direction=-1), name="j-calendar-shift-backward"),
    path('calendar/ajax/month/', CalendarMonthView.as_view(), name="j-calendar-month"),

    path('bible/', BibleView.as_view(), name="bible"),
    path('bible/book/<int:id>/', BookView.as_view(), name="book-id"),
    path('bible/book/<int:id>/chapter/<int:num>/', ChapterView.as_view(), name="chapter-id"),
    path('bible/book/<slug:slug>/', BookView.as_view(), name="book"),
    path('bible/book/<slug:slug>/chapter/<int:num>/', ChapterView.as_view(), name="chapter"),

    path('bible/lines/', LinesView.as_view(), name="lines"),

    path('volume/', VolumeListView.as_view(), name="volumes"),
    path('bible/volume/my/', MyVolumeListView.as_view(), name="volumes-my"),
    path('bible/volume/create/', csrf_protect(VolumeCreateView.as_view()),
         name="volume-create"),
    path('bible/volume/<int:id>/edit/', csrf_protect(VolumeEditView.as_view()),
         name="volume-edit"),
    path('bible/volume/<int:id>/remove/', VolumeRemoveView.as_view(),
         name="volume-del"),
    path('bible/volume/<int:id>/remove/confirm/', csrf_protect(VolumeRemoveView.as_view()),
         name="volume-del-confirm"),
    path('bible/volume/<int:id>/', VolumeView.as_view(), name="volume"),
    path('bible/volume/<int:id>/queue/', VolumeQueueView.as_view(), name="volume-queue"),
    path('bible/volume/<int:id>/chapter/<int:chid>/', ChapterVolumeView.as_view(),
         name="volume-chapter"),

    path('pray/<int:id>/', PrayView.as_view(), name="pray-id"),
    path('pray/<slug:slug>/', PrayView.as_view(), name="pray"),
    path('prayers/', PrayListView.as_view(), name="prayers"),

    path('psalter/', TemplateView.as_view(template_name="pray/psalter/main.html"), name="psalter"),
    path('psalter/begin/', TemplateView.as_view(template_name="pray/psalter/begin.html"),
         name="psalter-begin"),
    path('psalter/end/', TemplateView.as_view(template_name="pray/psalter/end.html"),
         name="psalter-end"),
    path('psalter/kathisma/<int:num>/', PsalterView.as_view(),
          name="kathisma"),

    path('communion/', CommunionView.as_view(), name="pray-communion"),
    path('easter/hours/', TemplateView.as_view(template_name="pray/easter/hours.html"),
          name="easter-hours"),
    path('morning/', MorningView.as_view(), name="pray-morning"),
    path('evening/', TemplateView.as_view(template_name="pray/evening.html"),
         name="pray-evening"),
    path('kanon/ave-maria/', KanonAveMariaView.as_view(), name="pray-ave-maria"),
    path('thanks/', TemplateView.as_view(template_name="pray/thanks.html"),
         name="pray-thanks"),
    path('holidays/', TemplateView.as_view(template_name="pray/holidays.html"),
         name="holidays"),
    path('troparion/', TroparionView.as_view(),
         name="troparion"),
    path('tropar/', TroparView.as_view(),
         name="tropar"),

    path('invite/confirm/', InviteConfirmView.as_view(), name="invite-confirm"),

    path('groups/ajax/edit/', login_required(group_access(csrf_protect(
                                GroupEditView.as_view()))),
         name="j-group-edit"),
    path('groups/create/', login_required(csrf_protect(GroupCreateView.as_view())),
         name="group-create"),
    path('groups/<int:id>/', login_required(group_access(GroupView.as_view())),
         name="group"),
    path('groups/<int:id>/ajax/', login_required(group_access(GroupView.as_view())),
         name="j-group"),
    path('groups/<int:id>/members/',
         login_required(group_access(GroupMembersView.as_view())),
         name="group-members"),
    path('groups/<int:id>/invite/',
         login_required(group_access(csrf_protect(GroupInviteView.as_view()))),
         name="group-invite"),
    path('groups/<int:id>/leave/',
         login_required(group_access(csrf_protect(
            TemplateView.as_view(template_name="groups/leave.html"),
         ))),
         name="group-leave"),
    path('groups/<int:id>/edit/', login_required(group_access(csrf_protect(
                                    GroupEditView.as_view()))),
         name="group-edit"),
    path('groups/<int:id>/queue/',
         login_required(group_access(GroupQueueView.as_view())),
         name="group-queue"),
    path('groups/<int:id>/list/',
         login_required(group_access(GroupListView.as_view())),
         name="group-list"),
    path('groups/<int:id>/reading/',
         login_required(group_access(GroupReadingView.as_view())),
         name="reading-group"),
    path('groups/<int:id>/reading/<int:year>/<int:month>/<int:day>/',
         login_required(group_access(GroupReadingView.as_view())),
         name="reading-group-date"),
    path('groups/<int:id>/epub/',
         login_required(group_access(EPubView.as_view())),
         name="epub-group"),

    path('reading/',
         login_required(TemplateView.as_view(template_name="reading/reading.html")),
         name="reading-user"),
    path('reading/today/',
         login_required(TemplateView.as_view(template_name="reading/reading_today.html")),
         name="reading-user-today"),
    path('reading/new/', GroupNewView.as_view(), name="reading-new"),
    path('reading/pub/', group_exist(ReadingView.as_view()), name="reading"),
    path('reading/pub/add/', login_required(csrf_protect(add_to_group)),
         name="add-to-group"),
    path('reading/pub/queue/', group_exist(QueueView.as_view()), name="reading-queue"),

    path('search/', SearchView.as_view(), name="search"),

    path('admin/', admin.site.urls),
    path('ajax/bible/', include('bible.ajax.urls')),
    path('forum/', include('forum.urls')),
]

