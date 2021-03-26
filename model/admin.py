from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from model.models import Profile, Country, Team, PermissionUser, Permission, Polls, Questions


class UserInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Доп. информация'


class PermissionInline(admin.StackedInline):
    model = PermissionUser
    can_delete = False
    verbose_name_plural = 'Роль пользователя'


class UserAd(UserAdmin):
    inlines = (UserInline, PermissionInline)


admin.site.unregister(User)
admin.site.register(User, UserAd)
admin.site.register(Country)
admin.site.register(Team)
admin.site.register(Permission)
admin.site.register(Polls)
admin.site.register(Questions)
