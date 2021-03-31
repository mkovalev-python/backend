import datetime

from django.contrib.auth.models import User
from rest_framework import permissions, status

from rest_framework.response import Response
from rest_framework.views import APIView

from api_v0.utils_views import save_poll_participant, save_poll_all, rating
from model.models import PermissionUser, Profile, Permission, Team, Country, Polls, Questions, Rating
from model.serializer import PermissionUserSerializer, ProfileSerializer, PermissionSerializer, TeamSerializer, \
    CountrySerializer, UserSerializerWithToken, PollsSerializer, RatingSerializer


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

        if request.query_params['permission'] == 'Participant':

            rating()

            queryset = Rating.objects.filter(username=request.user.username)
            serializer_rating = RatingSerializer(queryset, many=True).data

            return Response({'user': serializer_user, 'permission': serializer_permission,
                             'rating': serializer_rating})
        else:
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
            create_rating_field = Rating(username_id=request.data['username'],
                                         rating=Profile.objects.exclude(team='Staff').count(), points=0).save()
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
        req = request.data
        if req['info']['values']['category'] == 'participant':
            status = save_poll_participant(req)
        else:
            status = save_poll_all(req)

        return Response(status=status)


class GetActivePolls(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(in_archive=False, latePosting=False)
        serializer = PollsSerializer(queryset, many=True)
        return Response(serializer.data)


class GetLatePolls(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(in_archive=False, latePosting=True)
        serializer = PollsSerializer(queryset, many=True)
        return Response(serializer.data)


class GetArchivePolls(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(in_archive=True)
        serializer = PollsSerializer(queryset, many=True)
        return Response(serializer.data)


class GetViewPoll(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(id=request.query_params['id'])
        serializer_poll = PollsSerializer(queryset, many=True).data

        queryset = Questions.objects.filter(poll_id=request.query_params['id'])
        list_questions = []
        i = 0
        for item in queryset:
            question = item.question
            answer = item.answer.split(' ')
            if item.poll.category != 'participant':
                del answer[0]
            else:
                for i in range(int(answer[0])):
                    if i == 0:
                        answer.clear()
                    answer.append(i + 1)
            i += 1
            list_questions.append({'question': question, 'answer': answer, 'id': i})

        data = {'poll_info': serializer_poll, 'questions': list_questions}

        return Response(data)


class MovePolls(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        poll = Polls.objects.get(id=request.data['id'])
        if request.data['type'] == 'archive':
            poll.in_archive = True
            poll.save()
        if request.data['type'] == 'delete':
            poll.delete()
        if request.data['type'] == 'public':
            if poll.category == 'participant':
                if Polls.objects.filter(in_archive=False, latePosting=False, category='participant').exists():
                    poll_last = Polls.objects.get(in_archive=False, latePosting=False, category='participant')
                    poll_last.in_archive = True
                    poll_last.save()
            poll.latePosting = False
            poll.in_archive = False
            poll.datePosting = datetime.datetime.now()
            poll.save()
        return Response(status=status.HTTP_200_OK)
