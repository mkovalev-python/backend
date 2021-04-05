from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from api_v0.views import CheckPermission, GetUserInfo, GetListOption, PostCreateUser, GetUserList, DeleteUser, \
    CreateNewPoll, GetActivePolls, GetViewPoll, MovePolls, GetLatePolls, GetArchivePolls, GetTeam, GetPollTeam, \
    CheckPollTeam, GetPollsParticipant

urlpatterns = [
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
]
