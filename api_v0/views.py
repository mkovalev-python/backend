import datetime
import os
import random
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas
from django.http import FileResponse
from django.core import serializers
from django.contrib.auth.models import User
from rest_framework import permissions, status
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from api_v0.utils_views import save_poll_participant, save_poll_all, rating, points_my_team, save_poll, get_points, \
    add_points
from backend.settings import MEDIA_ROOT
from model.models import PermissionUser, Profile, Permission, Team, Country, Polls, Questions, Rating, SessionTC, \
    PollsCheck, QuestionsCheck, LogPoint, FileUpload, RatingTeam, Test, QuestionsTest, AnswersTest
from model.serializer import PermissionUserSerializer, ProfileSerializer, PermissionSerializer, TeamSerializer, \
    CountrySerializer, UserSerializerWithToken, PollsSerializer, RatingSerializer, SessionTCSerializer, \
    LogPointSerializer, QuestionsSerializer, QuestionsCheckSerializer, RatingTeamSerializer, TestSerializer
import pandas as pd


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
        status_session = SessionTCSerializer(SessionTC.objects.filter(number_session=serializer_user[0]['session']),
                                             many=True).data
        if request.query_params['permission'] == 'Participant':

            rating()

            queryset = Rating.objects.filter(username=request.user.username)
            serializer_rating = RatingSerializer(queryset, many=True).data

            queryset = RatingTeam.objects.get(team_id=request.user.profile.team_id,
                                              session_id=request.user.profile.session_id)
            serializer_rating_team = RatingTeamSerializer(queryset, many=False).data
            return Response({'user': serializer_user, 'permission': serializer_permission,
                             'rating': serializer_rating, 'status_session': status_session,
                             'rating_team': serializer_rating_team})
        else:
            return Response({'user': serializer_user, 'permission': serializer_permission})


class GetListOption(APIView):
    permissions_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset_permission = Permission.objects.all()
        queryset_team = Team.objects.all()
        queryset_country = Country.objects.all()
        queryset_session = SessionTC.objects.all()

        serializer_permission = PermissionSerializer(queryset_permission, many=True).data
        serializer_team = TeamSerializer(queryset_team, many=True).data
        serializer_country = CountrySerializer(queryset_country, many=True).data
        serializer_session = SessionTCSerializer(queryset_session, many=True).data

        return Response({'team': serializer_team,
                         'permission': serializer_permission,
                         'country': serializer_country,
                         'session': serializer_session})


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
                session_id=request.data['session']
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

        queryset = Test.objects.filter(in_archive=False, latePosting=False)
        serializerTest = TestSerializer(queryset, many=True)
        return Response(serializer.data + serializerTest.data)


class GetLatePolls(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(in_archive=False, latePosting=True)
        serializer = PollsSerializer(queryset, many=True)

        queryset = Test.objects.filter(in_archive=False, latePosting=True)
        serializerTest = TestSerializer(queryset, many=True)
        return Response(serializer.data + serializerTest.data)


class GetArchivePolls(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Polls.objects.filter(in_archive=True)
        serializer = PollsSerializer(queryset, many=True)

        queryset = Test.objects.filter(in_archive=True, )
        serializerTest = TestSerializer(queryset, many=True)
        return Response(serializer.data + serializerTest.data)


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
        try:
            if request.data['comp']:
                test = Test.objects.get(id=request.data['id'])
                if request.data['type'] == 'archive':
                    test.in_archive = True
                    test.save()
                if request.data['type'] == 'delete':
                    test.delete()
                if request.data['type'] == 'public':
                    test.latePosting = False
                    test.in_archive = False
                    test.save()
                return Response(status=status.HTTP_200_OK)
            else:
                poll = Polls.objects.get(id=request.data['id'])
                if request.data['type'] == 'archive':
                    if poll.category == 'participant' and poll.latePosting == False:
                        get_points(poll)
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
        except:
            poll = Polls.objects.get(id=request.data['id'])
            if request.data['type'] == 'archive':
                if poll.category == 'participant' and poll.latePosting == False:
                    get_points(poll)
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


class GetTeam(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        queryset = Profile.objects.filter(session_id=request.user.profile.session_id,
                                          team_id=request.user.profile.team_id,
                                          ).exclude(username=request.user.username)
        serializer = ProfileSerializer(queryset, many=True).data

        return Response(serializer)


class GetPollTeam(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        if request.query_params.__len__() == 1:
            category = 'participant'
        else:
            category = request.query_params['type']
        active_session = SessionTC.objects.get(active_session=True).number_session

        if category == 'participant':
            active_poll_team = Polls.objects.get(session_id=active_session, in_archive=False, category=category)
            check_poll_completed = PollsCheck.objects.filter(poll_id=active_poll_team.id,
                                                             poll_user_id=request.query_params['id'],
                                                             user_valuer_id=request.user.profile.id).exists()
        else:
            active_poll_team = Polls.objects.get(session_id=active_session, in_archive=False, category=category,
                                                 id=request.query_params['id'])
            check_poll_completed = PollsCheck.objects.filter(poll_id=active_poll_team.id,
                                                             user_valuer_id=request.user.profile.id).exists()
        if check_poll_completed:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            serializer = PollsSerializer(active_poll_team).data
            queryset = Questions.objects.filter(poll_id=active_poll_team.id)
            list_questions = []
            i = 0
            for item in queryset:
                question = item.question
                answer = item.answer.split(' ')
                if item.poll.category != 'participant':
                    del answer[0]
                else:
                    for i in range(int(answer[0]) + 1):
                        if i == 0:
                            answer.clear()
                        answer.append(i)
                i += 1
                list_questions.append({'question': question, 'answer': answer, 'id': i})

            data = {'poll_info': serializer, 'questions': list_questions}

            return Response(data)


class CheckPollTeam(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):

        if request.data.__len__() == 3:
            save_poll(request.data)
            return Response(status=status.HTTP_200_OK)
        else:
            poll = PollsCheck(poll_id=request.data['id_poll'], user_valuer_id=request.data['user_id'],
                              poll_user_id=request.data['user_poll_id'])
            poll.save()

            for el in request.data['answers']:
                get_id_question = Questions.objects.get(question=el).id
                QuestionsCheck(poll_id=request.data['id_poll'],
                               user_valuer_id=request.data['user_id'],
                               answer=request.data['answers'][el],
                               question_id=get_id_question,
                               poll_check_id=poll.id).save()

            add_points(request, poll)

            return Response(status=status.HTTP_200_OK)


class GetPollsParticipant(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        user_id = request.user.profile.id
        get_check_polls = PollsCheck.objects.filter(user_valuer_id=user_id)
        get_all_polls = Polls.objects.exclude(category='participant')
        get_all_polls = get_all_polls.exclude(session_id=0)
        for el in get_check_polls:
            get_all_polls = get_all_polls.exclude(id=el.poll_id)

        """Разделение по категориям"""
        list_category = ['service', 'spiker', 'other']
        data = dict.fromkeys(list_category)
        for i in list_category:

            polls = get_all_polls.filter(category=i, session_id=Profile.objects.get(id=user_id).session_id)
            serializer = PollsSerializer(polls, many=True).data
            if polls.count() == 0:
                continue
            else:
                data[i] = serializer

        return Response(data)


class GetAnalytics(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """Получение данных по логгера"""
        logger = LogPoint.objects.all()
        logger_list = []
        if logger.count() != 0:
            for log in logger:
                log_data = {
                    'name': log.username,
                    'points': log.points,
                    'date': log.date.strftime('%d/%m/%Y %H:%M:%S'),
                    'poll': log.poll
                }
                logger_list.append(log_data)

        """Получение данных по рейтингу участников"""
        rating = Rating.objects.all()
        rating_list = []
        for el in rating:
            user = Profile.objects.get(username=el.username).first_name + ' ' + \
                   Profile.objects.get(username=el.username).last_name

            data = {'rating': el.rating, 'points': el.points, 'user': user, 'team': el.username.profile.team_id,
                    'session': el.username.profile.session.number_session}

            rating_list.append(data)

        """Получение пройденных опросов и ответов"""
        serializer_user = ProfileSerializer(Profile.objects.all().exclude(team_id='Staff'), many=True).data
        i = 0
        for el_user in serializer_user:
            el_user['key'] = i
            j = 100000
            for el_poll in el_user['children']:
                serializer_questions = QuestionsSerializer(Questions.objects.filter(poll_id=el_poll['poll']),
                                                           many=True).data
                el_poll['children'] = serializer_questions
                id_poll = el_poll['poll']
                el_poll['key'] = j
                el_poll['poll'] = Polls.objects.get(id=el_poll['poll']).title
                ij = 10000000
                for el_questions in el_poll['children']:
                    el_questions['key'] = ij
                    el_questions['answer'] = ''
                    serializer_answers = QuestionsCheckSerializer(
                        QuestionsCheck.objects.filter(poll_id=id_poll, user_valuer_id=el_poll['user_valuer']),
                        many=True).data
                    for el_answers in serializer_answers:
                        el_answers['question'] = ''
                        el_answers['poll'] = ''
                    el_questions['children'] = serializer_answers
                    el_questions['poll'] = ''
                    ij += 1
                j += 1

            i += 1
        data = {'logger': logger_list, 'rating': rating_list, 'user': serializer_user}
        return Response(data)


class GetTableRating(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """Получение данных по рейтингу участников"""
        rating = Rating.objects.all()
        rating_list = []
        i = 1
        for el in rating:

            if int(request.query_params.__getitem__('session')) == el.username.profile.session.number_session:
                user = Profile.objects.get(username=el.username).first_name + ' ' + \
                       Profile.objects.get(username=el.username).last_name

                data = {'rating': i, 'points': el.points, 'user': user, 'team': el.username.profile.team_id}

                rating_list.append(data)
                i += 1
        data = {'rating': rating_list}

        return Response(data)


class GetTableRatingTeam(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """Получение данных по рейтингу команд"""
        all_users = Rating.objects.all()
        rating_list = []
        i = 1
        for el in all_users:
            if el.username.profile.session_id == int(request.query_params.__getitem__('session')):
                if el.username.profile.team_id == 'Веселые ребята':
                    user = Profile.objects.get(username=el.username).first_name + ' ' + \
                           Profile.objects.get(username=el.username).last_name
                    data = {'rating': i, 'points': el.points, 'user': user}
                    rating_list.append(data)
                    i += 1

        data = {'rating': rating_list}
        return Response(data)


class GetExcel(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """Скачивание файла из аналитики"""
        global file
        serializer = []
        if request.query_params['type'] == 'excel_log':
            queryset = LogPoint.objects.all()
            serializer = LogPointSerializer(queryset, many=True).data
            file = 'LoggerPoint_'
        if request.query_params['type'] == 'excel_rating':
            file = 'Rating_'
            queryset = Rating.objects.all()
            serializer = RatingSerializer(queryset, many=True).data

        df = pd.DataFrame(serializer)
        name = file + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + '.xlsx'
        df.to_excel(MEDIA_ROOT + '/file_excel/' + name)

        return Response({'url': '/images/media/file_excel/' + name})


class UploadUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """Получаем файл для загрузки из бд(Берется последний загруженный файл)"""
        file = FileUpload.objects.all().order_by('-id')[:1][0]
        exel_data_df = pandas.read_excel(file.file.path)
        for index, row in exel_data_df.iterrows():

            password = ''
            for x in range(8):
                password = password + random.choice(
                    list('1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))

            serializer = UserSerializerWithToken(
                data={'username': row['email'].split('@')[0], 'password': password})

            if serializer.is_valid():
                serializer.save()
                create_info_for_user = Profile(
                    first_name=row['Имя'],
                    last_name=row['Фамилия'],
                    country_id=row['Город'],
                    team_id=row['Команда'],
                    birthday='2021-05-01',
                    username_id=row['email'].split('@')[0],
                    session_id=row['Смена']
                ).save()
                create_permission_for_user = PermissionUser(
                    permission_id='Participant',
                    username_id=row['email'].split('@')[0]).save()
                create_rating_field = Rating(username_id=row['email'].split('@')[0],
                                             rating=Profile.objects.exclude(team='Staff').count(), points=0).save()

            """Отправка письма с данными для входа"""

            message = MIMEMultipart()
            message['Subject'] = 'Параметры для входа в систему опросов ТС'
            message['From'] = 'mkovalev@hse.ru'
            message['To'] = row['email']

            html = """\
                    <html>
                        <head></head>
                        <body>
                        <h4>Здравствуйте! Вы были зарегистрированы в системе опросов форума "Территория Смыслов".</h4>
                        
                        <span><b>Login:</b>  """ + row['email'].split('@')[0] + """</span><br>
                        <span><b>Password:</b>  """ + password + """</span></body></html>"""

            text = MIMEText(html, 'html')
            message.attach(text)

            port = 587
            smtp_server = "smtp.hse.ru"

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                try:
                    server.login('mkovalev', '!N7DU935')
                    server.sendmail(message['From'], message['To'], message.as_string())
                    server.quit()
                except:
                    return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response(status=status.HTTP_202_ACCEPTED)


class CreateTest(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            test = Test(title=request.data['values']['name'],
                        description=request.data['values']['description'],
                        points=request.data['values']['points'],
                        session_id=request.data['values']['session'],
                        num_comp_id=int(request.data['values']['numComp']))
            test.save()
            for el in request.data['listQuestions']:
                question = QuestionsTest(question=el['question'], test_id=test.id)
                question.save()
                for i in el['answers']:
                    answer = AnswersTest(answer=i['answer'], points=i['point'], question_id=question.id)
                    answer.save()

            return Response(status=status.HTTP_201_CREATED)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
