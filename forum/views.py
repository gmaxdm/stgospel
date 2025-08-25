import os
import logging
from unidecode import unidecode

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.db.utils import IntegrityError
from django.conf import settings

from gospel.json import LazyEncoder

from forum.models import (Category, Forum, Topic, Post, PostLike,
                          DirtyWord)


logger = logging.getLogger(__name__)


def get_lang(code):
    return code.split("-")[0]


@csrf_protect
def index(request):
    """Main forums topics listing with particular locale."""
    try:
        locale = request.GET["lang"]
        if locale not in settings.FORUM_LANGS_CODES:
            raise ValueError
    except (KeyError, ValueError):
        if request.user.is_authenticated:
            locale = request.user.locale
        else:
            locale = get_lang(settings.LANGUAGE_CODE)

    forums = []
    forums_ids = []
    for forum in Forum.objects.filter(visible=True, locale=locale):
        forums.append(forum)
        forums_ids.append(forum.id)

    topics = Topic.objects.get_topics(forums_ids)

    return render(request, "forum/index.html", {
        'topics': topics,
        'forums': forums,
    })


@csrf_protect
def forum(request, slug):
    """Filtering topics by forum."""
    try:
        forum = Forum.objects.select_related().get(slug=slug)
    except Forum.DoesNotExist:
        raise Http404

    forums = [forum]
    forums_ids = [forum.id]

    topics = Topic.objects.get_topics(forums_ids)

    return render(request, "forum/index.html", {
        'topics': topics,
        'forums': forums,
    })


def topic(request, slug, topic_slug):
    """Show topic"""
    try:
        topic = Topic.objects.select_related().get(slug=topic_slug,
                                                   forum__slug=slug)
    except Topic.DoesNotExist:
        raise Http404

    topic.inc_visits()
    topic.save(update_fields=["visits"])

    return render(request, "forum/topic.html", {
        "topic": topic,
    })


def posts(request):
    """Show topic's posts"""
    try:
        topic_id = int(request.GET["t"])
        topic = Topic.objects.get(id=topic_id)
    except (KeyError, TypeError, ValueError, Topic.DoesNotExist):
        return JsonResponse({"error": "no topic"})

    user_id = 0
    if request.user.is_authenticated:
        user_id = request.user.id

    posts = []
    for post in Post.objects.posts_with_emotions(topic_id, user_id):
        post.can_edit = post.user_id == user_id and not post.deleted
        posts.append(post)

    return JsonResponse({
        "ro": int(topic.closed or not request.user.is_authenticated),
        "posts": posts
    }, encoder=LazyEncoder)


@login_required
def close_topic(request, slug, topic_slug):
    try:
        topic = Topic.objects.get(slug=topic_slug,
                                  forum__slug=slug)
    except Topic.DoesNotExist:
        raise Http404
    topic.closed = True
    topic.save(update_fields=["closed"])
    return HttpResponseRedirect(reverse('forum-topic', args=(slug, topic_slug)))


@login_required
def new_topic(request):
    _resp = HttpResponseRedirect(reverse('forum-index'))
    if request.method == 'POST':
        try:
            forum = Forum.objects.get(id=request.POST["forum"])
        except (KeyError, Forum.DoesNotExist):
            return _resp

        try:
            title = request.POST["title"]
            title = DirtyWord.clean(title)
            slug = slugify(unidecode(title))
            if not title or not slug:
                raise ValueError
        except (KeyError, ValueError):
            return _resp

        try:
            topic = Topic.objects.create(
                title=title,
                slug=slug,
                forum=forum,
                creator=request.user
            )
        except IntegrityError:
            # check if topic with this slug already exists
            messages.error(request, _("Topic with the same slug already exists"))
            return _resp

        return HttpResponseRedirect(reverse("forum-topic",
                                            args=(forum.slug, slug)))

    return _resp


@login_required
def post_edit(request):
    if request.method == 'POST':
        try:
            topic = Topic.objects.get(id=int(request.POST["t"]))
        except (KeyError, TypeError, ValueError, Topic.DoesNotExist):
            return JsonResponse({"error": "topic doesn't exist"})

        if topic.closed:
            return JsonResponse({"error": "topic is closed"})

        try:
            msg = request.POST["msg"]
            msg = DirtyWord.clean(msg)
            if not msg:
                raise ValueError
        except (KeyError, ValueError):
            return JsonResponse({"error": "no message"})

        if "post" in request.POST:
            try:
                post_id = int(request.POST["post"])
                post = Post.objects.get(id=post_id)
                if post.deleted or post.user_id != request.user.id:
                    raise ValueError
            except (TypeError, ValueError, Post.DoesNotExist):
                return JsonResponse({"error": "forbidden"})

            post.body = msg
            post.changed = True
            post.moderated = False
            post.save()
        else:
            post = Post.objects.create(
                topic=topic,
                body=msg,
                user=request.user,
                user_ip=request.META['REMOTE_ADDR']
            )
        post.can_edit = True

    return JsonResponse({"post": post}, encoder=LazyEncoder)


@login_required
def post_delete(request):
    if request.method != 'POST':
        return JsonResponse({"error": "not allowed"})

    try:
        post_id = int(request.POST["post"])
        post = Post.objects.get(id=post_id)
        if post.deleted or post.user_id != request.user.id:
            return JsonResponse({"error": "permission denied"})
    except (KeyError, TypeError, ValueError, Post.DoesNotExist):
        return JsonResponse({"error": "post not found"})

    post.deleted = True
    post.save()

    return JsonResponse({"ok": 1})


@login_required
def post_like(request):
    if request.method != 'POST':
        return JsonResponse({"error": "not allowed"})

    try:
        post_id = int(request.POST["post"])
        post = Post.objects.get(id=post_id)
    except (KeyError, ValueError, TypeError, Post.DoesNotExist):
        return JsonResponse({"error": "post bot found"})

    likes = post.like
    try:
        pl = PostLike.objects.get(post_id=post_id,
                                  user_id=request.user.id)
        if pl.emotion == "N":
            pl.emotion = "L"
            em = "L"
            likes += 1
        elif pl.emotion == "L":
            pl.emotion = "N"
            em = "N"
            likes -= 1
        pl.save()
    except PostLike.DoesNotExist:
        PostLike.objects.create(post_id=post_id,
                                user_id=request.user.id,
                                emotion="L")
        em = "L"
        likes += 1

    _res = (likes - post.like)
    if post.like + _res < 0:
        post.like = 0
    else:
        post.like = F("like") + _res
    post.save(update_fields=["like"])
    return JsonResponse({"em": em, "likes": likes})


@login_required
def upload_img(request):
    if request.method == 'POST':
        try:
            img = request.FILES["img"]
            if img.size > settings.IMAGE_SIZE:
                raise ValueError

            name, ext = os.path.splitext(os.path.basename(img.name))
            if ext[1:].lower() not in settings.IMAGE_EXT:
                raise TypeError

            _file_name = "{}_{}{}".format(name, get_random_string(7), ext)
            with open(os.path.join(settings.MEDIA_ROOT, settings.FORUM_UPLOAD_PATH,
                                   _file_name), "wb") as f:
                f.write(img.read())
            return JsonResponse({"location": os.path.join(settings.MEDIA_URL,
                                                          settings.FORUM_UPLOAD_PATH,
                                                          _file_name)})
        except (KeyError, ValueError, TypeError):
            pass
    return HttpResponseForbidden()

