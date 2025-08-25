import os

from django.contrib import messages
from django.contrib import admin
from django.contrib.admin.options import (unquote, csrf_protect_m,
                                          HttpResponseRedirect)

from forum.models import Category, Forum, Topic, Post


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "forums", "order")
    exclude = ("forums",)


class ForumAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "category", "topics", "creator", "cdate")
    prepopulated_fields = {"slug": ("title",)}
    exclude = ("topics",)

    def save_model(self, request, obj, form, change):
        _new_img = form.cleaned_data["img"]
        if _new_img:
            name, _ = os.path.splitext(os.path.basename(str(_new_img)))
            if name not in obj.img32:
                obj.save_imgs()
        obj.creator = request.user
        super().save_model(request, obj, form, change)


class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "posts", "visits", "rate", "creator", "cdate", "closed")
    list_filter = ("creator",)
    prepopulated_fields = {"slug": ("title",)}
    exclude = ("visits", "rate", "posts")

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        super().save_model(request, obj, form, change)


class PostAdmin(admin.ModelAdmin):
    search_fields = ("user",)
    list_filter = ("moderated",)
    list_display = ("topic", "like", "user", "moderated", "deleted", "cdate")
    raw_id_fields = ('user', 'topic')
    exclude = ('moderated', "like")

    change_form_template = 'forum/admin_change_post.html'

    actions = ["make_moderated"]

    def make_moderated(self, request, queryset):
        cnt = 0
        for item in queryset.all():
            item.approve()
            cnt += 1

        msg = f"Moderated {cnt} posts"
        self.message_user(request, msg, messages.SUCCESS)
    make_moderated.short_description = "Mark selected posts as moderated"
    make_moderated.allowed_permissions = ('change',)

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if request.method == 'POST' and '_make_moderated' in request.POST:
            obj = self.get_object(request, unquote(object_id))
            obj.approve()
            return HttpResponseRedirect(request.get_full_path())

        return admin.ModelAdmin.changeform_view(self, request, object_id=object_id,
                                                form_url=form_url,
                                                extra_context=extra_context)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)

