import os
import re
import datetime
import binascii

from PIL import Image
from django.db import models
from django.db.models import F, Q
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django.utils.formats import date_format
from django.conf import settings

from authuser.models import User


RE_WORD = re.compile(r"\w+")


POSTS_PER_PAGE = getattr(settings, 'POSTS_PER_PAGE', 10)


def encode64(msg):
    """return encoded string
        cutting last new line char
    """
    return binascii.b2a_base64(msg.encode("utf8"), newline=False).decode("utf8")


def decode64(msg):
    """return decoded string
    """
    return binascii.a2b_base64(msg).decode("utf8")


def get_upload_path(instance, filename):
    return os.path.join("images", instance.upload_to_subdir, filename)


class ImageFieldMixin(models.Model):
    upload_to_subdir = "forum"

    img = models.ImageField(upload_to=get_upload_path, null=True, blank=True)
    img32 = models.CharField(max_length=255, default=settings.DEFAULT_32)
    img128 = models.CharField(max_length=255, default=settings.DEFAULT_128)

    class Meta:
        abstract = True

    def save_imgs(self, *args, **kwargs):
        if self.img:
            # upload_to path doesn't exist in self.img
            # need to save the model to get the full path applied
            self.save(*args, **kwargs)

            _dir = os.path.dirname(self.img.file.name)
            dir_32 = os.path.join(_dir, "32")
            os.makedirs(dir_32, exist_ok=True)
            dir_128 = os.path.join(_dir, "128")
            os.makedirs(dir_128, exist_ok=True)

            name, ext = os.path.splitext(os.path.basename(self.img.file.name))
            if ext[1:].lower() in settings.IMAGE_EXT:
                _file_name = "{}_{}{}".format(name, get_random_string(7), ext)
                img = Image.open(self.img)
                # for Pillow < 9.0.0
                img128 = img.resize((128, 128), Image.LANCZOS)
                # for Pillow > 9.0.0
                #img128 = img.resize((128, 128), Image.Resampling.LANCZOS)
                img128.save(os.path.join(dir_128, _file_name), quality=100)
                # for Pillow < 9.0.0
                img32 = img128.resize((32, 32), Image.LANCZOS)
                # for Pillow > 9.0.0
                #img32 = img128.resize((32, 32), Image.Resampling.LANCZOS)
                img32.save(os.path.join(dir_32, _file_name), quality=100)
                _url = os.path.dirname(self.img.url)
                self.img128 = os.path.join(_url, "128", _file_name)
                self.img32 = os.path.join(_url, "32", _file_name)

    def _create_img_urls(self):
        url = self.img.url
        dirname = os.path.dirname(url)
        basename = os.path.basename(url)
        name, ext = os.path.splitext(basename)
        name32 = "{}32".format(name)
        name128 = "{}128".format(name)
        url32 = os.path.join(dirname, "32", "{}{}".format(name32, ext))
        url128 = os.path.join(dirname, "128", "{}{}".format(name128, ext))


class Category(models.Model):
    order = models.IntegerField()
    title = models.CharField(max_length=60)
    forums = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return self.title


class Forum(ImageFieldMixin):
    title = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, default='')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    udate = models.DateTimeField(auto_now=True)
    cdate = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    locale = models.CharField(_('Язык'), choices=settings.FORUM_LANGS,
                              max_length=2, default='ru')
    visible = models.BooleanField(default=True)
    topics = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["locale"], name="locale_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.id is None:
            self.category.forums = F("forums") + 1
            self.category.save(update_fields=["forums"])
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_summary(self):
        if len(self.description) > 50:
            return self.description[:50] + '...'
        return self.description

    def get_visits(self):
        vs = 0
        for t in self.topic_set.all():
            vs += t.visits
        return vs

    def has_seen(self, user=None):
        if user.is_authenticated():
            for t in self.topic_set.all():
                if not t.has_seen(user):
                    return False
        return True

    def num_posts(self):
        return sum([t.num_posts() for t in self.topic_set.all()])

    def num_topics(self):
        return self.topic_set.all().count()


class TopicManager(models.Manager):

    def get_topics(self, forums_ids):
        # LEFT OUTER JOIN
        return (Topic.objects.select_related("forum", "creator",
                                             "forum__category",
                                             "last_post",
                                             "last_post__user")
                   .filter(forum_id__in=forums_ids)
                   .order_by('forum__category__order'))


class Topic(models.Model):
    title = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    description = models.TextField(max_length=5000, blank=True, null=True)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    cdate = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    udate = models.DateTimeField(auto_now=True)
    closed = models.BooleanField(blank=True, default=False)
    visits = models.IntegerField(default=0)
    rate = models.IntegerField(default=0)
    posts = models.PositiveIntegerField(default=0)
    last_post = models.ForeignKey("Post", null=True, blank=True, related_name="+",
                                  on_delete=models.SET_NULL)

    objects = TopicManager()

    def save(self, *args, **kwargs):
        if self.id is None:
            self.forum.topics = F("topics") + 1
            self.forum.save(update_fields=["topics"])
        super().save(*args, **kwargs)

    def inc_visits(self):
        self.visits = F("visits") + 1

    def __str__(self):
        return f"{self.title} ({self.creator})"


class PostManager(models.Manager):

    def posts_with_emotions(self, topic_id, user_id):
        return self.model.objects.raw("""SELECT * FROM forum_post p
    INNER JOIN `authuser_user` ON (p.`user_id` = `authuser_user`.`id`)
    LEFT OUTER JOIN forum_postlike pl ON p.id=pl.post_id AND pl.user_id = %s
    WHERE (p.`topic_id` = %s AND (p.`moderated` OR p.`user_id` = %s))
    ORDER BY p.`cdate` ASC
    """, [user_id, topic_id, user_id])

    def get_posts(self, topic_id, user_id):
        return (Post.objects.select_related("user")
                    .filter(Q(topic_id=topic_id), Q(moderated=True) | Q(user_id=user_id))
                    .order_by("cdate"))


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    body = models.TextField(max_length=5000)
    like = models.PositiveIntegerField(default=0)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    telegram_id = models.CharField(max_length=20, blank=True, null=True)
    cdate = models.DateTimeField(auto_now_add=True)
    udate = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=False)
    moderated = models.BooleanField(default=False)
    changed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    emotion = "N"
    can_edit = False

    objects = PostManager()

    def save(self, *args, **kwargs):
        if self.id is None:
            self.user.posts = F("posts") + 1
            self.user.save(update_fields=["posts"])
            self.topic.posts = F("posts") + 1
            self.topic.save(update_fields=["posts"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.topic} ({self.user})"

    def to_json(self):
        return {
            "id": self.id,
            "tid": self.topic_id,
            "user": str(self.user),
            "msg": "" if self.deleted else encode64(self.body),
            "like": self.like,
            "mod": int(self.moderated),
            "edit": int(self.changed),
            "del": int(self.deleted),
            "ce": int(self.can_edit),
            "emotion": self.emotion or "N",
            "cdate": date_format(self.cdate, use_l10n=True),
        }

    def approve(self):
        if self.moderated:
            return

        self.moderated = True
        self.save(update_fields=["moderated"])
        if self.topic.last_post_id is None or self.cdate >= self.topic.last_post.cdate:
            self.topic.last_post = self
            self.topic.save(update_fields=["last_post"])

    def get_post_num(self):
        return Post.objects.filter(topic__id=self.topic_id).filter(cdate__lt=self.cdate).count()

    def get_page(self):
        return self.get_post_num() / POSTS_PER_PAGE + 1

    def short(self):
        return "%s - %s" % (self.user, self.cdate.strftime("%Y-%m-%d %H:%M"))

    def get_absolute_url(self):
        return '/%s?page=%d#%d' % (self.topic.id, self.get_page(), self.id)

    short.allow_tags = True


EMOTIONS = (
    ("N", _("None")),
    ("L", _("Like")),
)


class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    emotion = models.CharField(choices=EMOTIONS, max_length=1, default="N")


class DirtyWord(models.Model):
    word = models.CharField(max_length=100)
    cdate = models.DateTimeField(default=datetime.datetime.now)

    hide_string = "***"

    @classmethod
    def words(cls):
        if hasattr(cls, "_words"):
            return cls._words
        _words = set()
        for w in DirtyWord.objects.all():
            _words.add(w.word)
        cls._words = _words
        return cls._words

    @classmethod
    def clean(cls, text):
        dirty = cls.words()
        _words_to_replace = []
        for word in RE_WORD.findall(text):
            if word.lower() in dirty:
                _words_to_replace.append(word)

        new_text = text
        for word in _words_to_replace:
            new_text = new_text.replace(word, cls.hide_string)
        return new_text

    @classmethod
    def is_empty(cls, text):
        return text.replace(cls.hide_string, "").strip() == ""


    def __str__(self):
        return self.word

