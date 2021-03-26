from django.contrib.auth.models import User
from rest_framework import permissions, status

from rest_framework.response import Response
from rest_framework.views import APIView

from model.models import PermissionUser, Profile, Permission, Team, Country, Polls, Questions
from model.serializer import PermissionUserSerializer, ProfileSerializer, PermissionSerializer, TeamSerializer, \
    CountrySerializer, UserSerializerWithToken


class CheckPermission(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = PermissionUser.objects.filter(username=request.user.username)
        serializer = PermissionUserSerializer(queryset, many=True).data

        return Response(serializer)


class GetUserInfo(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Profile.objects.filter(username=request.user.username)
        serializer_user = ProfileSerializer(queryset, many=True).data
        get_permission_name = Permission.objects.filter(slug=request.query_params['permission'])
        serializer_permission = PermissionSerializer(get_permission_name, many=True).data

        return Response({'user': serializer_user, 'permission': serializer_permission})


class GetListOption(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset_permission = Permission.objects.all()
        queryset_team = Team.objects.all()
        queryset_country = Country.objects.all()

        serializer_permission = PermissionSerializer(queryset_permission, many=True).data
        serializer_team = TeamSerializer(queryset_team, many=True).data
        serializer_country = CountrySerializer(queryset_country, many=True).data
        return Response({'team': serializer_team, 'permission': serializer_permission, 'country': serializer_country})


class PostCreateUser(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):

        serializer = UserSerializerWithToken(
            data={'username': request.data['username'], 'password': request.data['password']})

        if serializer.is_valid():
            serializer.save()
            create_info_for_user = Profile(
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                birthday=request.data['birthday'].split('T')[0],
                country_id=request.data['country'],
                team_id=request.data['team'],
                username_id=request.data['username'],
            ).save()
            create_permission_for_user = PermissionUser(
                permission_id=request.data['permission'],
                username_id=request.data['username']).save()
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response(status=status.HTTP_201_CREATED)


class GetUserList(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        username = User.objects.all()
        data = []
        for username in username:
            dict_user = {}
            user_info = Profile.objects.get(username_id=username.username)
            user_permission = PermissionUser.objects.get(username_id=username.username)

            dict_user = {
                'username': username.username,
                'first_name': user_info.first_name,
                'last_name': user_info.last_name,
                'birthday': user_info.birthday,
                'country': user_info.country_id,
                'team': user_info.team_id,
                'permission': user_permission.permission.name
            }

            data.append(dict_user)
        return Response(data)


class DeleteUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def delete(request):
        User.objects.filter(username=request.data['username']).delete()
        Profile.objects.filter(username_id=request.data['username']).delete()
        PermissionUser.objects.filter(username_id=request.data['username']).delete()

        return Response(status=status.HTTP_202_ACCEPTED)


class CreateNewPoll(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):

        if request.data['info']['latePosting']:
            create_poll = Polls(title=request.data['info']['title'],
                                description=request.data['info']['description'],
                                category=request.data['info']['category'],
                                latePosting=request.data['info']['latePosting'],
                                datePosting=request.data['info']['datePosting']).save()
        else:
            create_poll = Polls(title=request.data['info']['title'],
                                description=request.data['info']['description'],
                                category=request.data['info']['category']).save()

        for question in request.data['questions']:
            str_answer = ''
            for answer in question['answers']:
                str_answer += ' ' + answer['answer']

            create_question = Questions(poll_id=Polls.objects.get(title=request.data['info']['title'],
                                                                  description=request.data['info']['description']).id,
                                        question=question['question'],
                                        answer=str_answer).save()

        return Response(status=status.HTTP_201_CREATED)
