from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from django.conf.urls.static import static
from api_v0.views import CheckPermission, GetUserInfo, GetListOption, PostCreateUser, GetUserList, DeleteUser, \
    CreateNewPoll, GetActivePolls, GetViewPoll, MovePolls, GetLatePolls, GetArchivePolls, GetTeam, GetPollTeam, \
    CheckPollTeam, GetPollsParticipant, GetAnalytics, GetExcel, UploadUser, GetTableRating, GetTableRatingTeam, \
    CreateTest, GetTests, AnaliticNew, CreateStartInfo, GetUsersInfo, PullPoints, SearchUser, SendNewPass, Edit, \
    DelUsers, PostPassword
from backend import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('token/obtain/', obtain_jwt_token),
    path('token/refresh/', refresh_jwt_token),
    path('check/permission/', CheckPermission.as_view()),
    path('get/user/info/', GetUserInfo.as_view()),
    path('get/list/option/', GetListOption.as_view()),
    path('post/create/user/', PostCreateUser.as_view()),
    path('get/user/list/', GetUserList.as_view()),
    path('delete/user/', DeleteUser.as_view()),
    path('create/new/poll/', CreateNewPoll.as_view()),
    path('get/active/polls/', GetActivePolls.as_view()),
    path('get/view/poll/', GetViewPoll.as_view()),
    path('move/polls/', MovePolls.as_view()),
    path('get/late/polls/', GetLatePolls.as_view()),
    path('get/archive/polls/', GetArchivePolls.as_view()),
    path('get/team/', GetTeam.as_view()),
    path('get/poll/team/', GetPollTeam.as_view()),
    path('check/poll/team/', CheckPollTeam.as_view()),
    path('get/poll/', GetPollsParticipant.as_view()),
    path('get/analytics/1', GetAnalytics.as_view()),
    path('get/analytics/', AnaliticNew.as_view()),
    path('get/table_rating/', GetTableRating.as_view()),
    path('get/table_rating_team/', GetTableRatingTeam.as_view()),
    path('get/excel/', GetExcel.as_view()),
    path('upload_user/', UploadUser.as_view()),
    path('post/test/', CreateTest.as_view()),
    path('get/tests/', GetTests.as_view()),
    path('create/start/info/', CreateStartInfo),
    path('get/users/info/', GetUsersInfo.as_view()),
    path('pull/points/', PullPoints.as_view()),
    path('search/user/', SearchUser.as_view()),
    path('send/new/password/', SendNewPass.as_view()),
    path('edit/', Edit.as_view()),
    path('del_userss/', DelUsers.as_view()),
    path('post/password/', PostPassword.as_view())
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
