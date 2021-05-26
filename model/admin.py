from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from model.models import Profile, Country, Team, PermissionUser, Permission, Polls, Questions, Rating, SessionTC, \
    PollsCheck, QuestionsCheck, FileUpload, RatingTeam


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


class SessionTCAdmin(admin.ModelAdmin):
    model = SessionTC
    list_display = ['number_session', 'name_session', 'date_from_session', 'date_to_session', 'active_session']


class PollsCheckAdmin(admin.ModelAdmin):
    model = PollsCheck
    list_display = ['user_valuer', 'poll_user', 'poll']


admin.site.unregister(User)
admin.site.register(User, UserAd)
admin.site.register(Country)
admin.site.register(Team)
admin.site.register(Permission)
admin.site.register(Polls)
admin.site.register(Questions)
admin.site.register(Rating)
admin.site.register(SessionTC, SessionTCAdmin)
admin.site.register(PollsCheck, PollsCheckAdmin)
admin.site.register(QuestionsCheck)
admin.site.register(FileUpload)
admin.site.register(RatingTeam)