from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from model.models import Profile, Country, Team


class UserInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Доп. информация'
    readonly_fields = ["preview"]

    @staticmethod
    def preview(obj):
        return mark_safe(f'<img src="{obj.image.url}" height="100" width="100">')


class UserAd(UserAdmin):
    inlines = (UserInline,)


admin.site.unregister(User)
admin.site.register(User, UserAd)
admin.site.register(Country)
admin.site.register(Team)
