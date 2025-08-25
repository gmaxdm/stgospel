from django.contrib import admin
from .models import User, Feedback


class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'groups', 'date_joined')
    ordering = ('username',)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('msg', 'user', 'cdate')
    list_filter = ('cdate', 'user')


admin.site.register(User, UserAdmin)
admin.site.register(Feedback)

