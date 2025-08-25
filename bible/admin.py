from django.contrib import admin
from .models import (Book, Pray, Volume)


class PrayAdmin(admin.ModelAdmin):
    fields = ("title", "text")


class VolumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'creater', 'cdate')
    list_filter = ('cdate', 'mdate')


admin.site.register(Book)
admin.site.register(Pray, PrayAdmin)
admin.site.register(Volume, VolumeAdmin)

