from django.contrib import admin
from .models import *


class AgreementGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'cdate', 'mdate', 'public', 'users_count')
    list_filter = ('cdate', 'public')
    ordering = ('cdate',)

    def users_count(self, obj):
        return obj.users.count()


class CounterAdmin(admin.ModelAdmin):
    list_display = ('path', 'count')
    ordering = ('-count',)


admin.site.register(AgreementGroup, AgreementGroupAdmin)
admin.site.register(AgreementGroupUser)
admin.site.register(PrayFor)
admin.site.register(PrayGroup)
admin.site.register(Counter, CounterAdmin)

