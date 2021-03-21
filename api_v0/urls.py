from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from api_v0.views import CheckPermission, GetUserInfo, GetListOption, PostCreateUser

urlpatterns = [
    path('token/obtain/', obtain_jwt_token),
    path('token/refresh/', refresh_jwt_token),
    path('check/permission/', CheckPermission.as_view()),
    path('get/user/info/', GetUserInfo.as_view()),
    path('get/list/option/', GetListOption.as_view()),
    path('post/create/user/', PostCreateUser.as_view()),
]
