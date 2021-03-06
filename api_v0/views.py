import datetime
import os
import random
import smtplib
import ssl
import string
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import chain

from django.db.models import Sum
from datetime import datetime, timedelta
import pandas
from django.http import FileResponse
from django.core import serializers
from django.contrib.auth.models import User
from rest_framework import permissions, status
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from api_v0.utils_views import save_poll_participant, save_poll_all, rating, points_my_team, save_poll, get_points, \
    add_points, countAnswers
from backend.settings import MEDIA_ROOT
from model.models import PermissionUser, Profile, Permission, Team, Country, Polls, Questions, Rating, SessionTC, \
    PollsCheck, QuestionsCheck, LogPoint, FileUpload, RatingTeam, Test, QuestionsTest, AnswersTest, CheckTest, \
    QuestionsCheckTest, SmtpServer
from model.serializer import PermissionUserSerializer, ProfileSerializer, PermissionSerializer, TeamSerializer, \
    CountrySerializer, UserSerializerWithToken, PollsSerializer, RatingSerializer, SessionTCSerializer, \
    LogPointSerializer, QuestionsSerializer, QuestionsCheckSerializer, RatingTeamSerializer, TestSerializer, \
    QuestionsCheckSerializerTest
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
            get_team = Profile.objects.filter(team_id=request.user.profile.team_id,
                                              session_id=request.user.profile.session_id).count()

            """???????????????????? ???????????????????????? ??????????????"""
            get_active_session = SessionTC.objects.get(active_session=True)
            get_active_team = RatingTeam.objects.filter(session_id=get_active_session.number_session)
            koef_user = 0
            for team in get_active_team:
                get_users = Profile.objects.filter(session_id=get_active_session.number_session, team_id=team.team)
                points = 0
                for user in get_users:
                    points += Rating.objects.get(username_id=user.username).points
                try:
                    koef_user += points / get_users.count()
                except:
                    continue
            try:
                koef_team = (serializer_rating_team.__getitem__('points') / get_team) / (
                        koef_user / get_active_team.count())
            except ZeroDivisionError:
                koef_team = 0
            try:
                koef_user = serializer_rating.__getitem__(0)['points'] / (
                        serializer_rating_team.__getitem__('points') / get_team)
            except ZeroDivisionError:
                koef_user = 0
            return Response({'user': serializer_user, 'permission': serializer_permission,
                             'rating': serializer_rating, 'status_session': status_session,
                             'rating_team': serializer_rating_team, 'koef_user': koef_user,
                             'koef_team': round(koef_team, 2)})
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
            data={'username': request.data['username'].split('@')[0], 'password': request.data['password'],
                  'email': request.data['username']})

        if serializer.is_valid():
            serializer.save()
            create_info_for_user = Profile(
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                birthday=request.data['birthday'].split('T')[0],
                country_id=request.data['country'],
                team_id=request.data['team'],
                username_id=request.data['username'].split('@')[0],
                session_id=request.data['session']
            ).save()
            create_permission_for_user = PermissionUser(
                permission_id=request.data['permission'],
                username_id=request.data['username'].split('@')[0]).save()
            if request.data['permission'] != 'Staff':
                create_rating_field = Rating(username_id=request.data['username'].split('@')[0],
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
            try:
                user_info = Profile.objects.get(username_id=username.username)
            except:
                continue
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
        get_all_session = SessionTC.objects.all().exclude(number_session=0)
        data = {}
        for session in get_all_session:
            queryset = Polls.objects.filter(in_archive=True, session_id=session.number_session)
            serializer = PollsSerializer(queryset, many=True)

            queryset1 = Test.objects.filter(in_archive=True, session_id=session.number_session)
            serializerTest = TestSerializer(queryset1, many=True)
            data[session.number_session] = serializer.data + serializerTest.data
        return Response(data)


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
            answer = item.answer.split('|')
            if item.poll.category != 'participant':
                del answer[0]
            else:
                for i in range(int(answer[0])):
                    if i == 0:
                        answer.clear()
                    answer.append(i + 1)
            i += 1
            list_questions.append({'question': question, 'answer': answer, 'id': i, 'freeAnswer': item.freeAnswer})

        data = {'poll_info': serializer_poll, 'questions': list_questions}

        return Response(data)


class MovePolls(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            if request.data['comp']:
                test = Test.objects.get(id=request.data['id'])
                if request.data['type'] == 'copy':
                    test_copy = Test(in_archive=False,
                                     description=test.description,
                                     latePosting=True,
                                     num_comp_id=test.num_comp_id,
                                     points=test.points,
                                     session_id=SessionTC.objects.get(active_session=True).number_session,
                                     title=test.title
                                     )
                    test_copy.save()
                    '''?????????????????????? ???????????????? ?? ??????????????'''
                    questions = QuestionsTest.objects.filter(test_id=test.id)
                    for question in questions:
                        copy_question = QuestionsTest(question=question.question, test_id=test_copy.id)
                        copy_question.save()

                        answers = AnswersTest.objects.filter(question_id=question.id)
                        for answer in answers:
                            copy_answer = AnswersTest(answer=answer.answer, points=answer.points,
                                                      question_id=copy_question.id)
                            copy_answer.save()
                    return Response(status=status.HTTP_200_OK)
                if request.data['type'] == 'report':
                    get_answer = QuestionsCheckTest.objects.filter(poll_id=test.id)
                    listAnswers = []
                    for answer in get_answer:
                        data = {
                            '??????': answer.user_valuer.first_name + ' ' + answer.user_valuer.last_name,
                            '????????????': answer.question.question,
                            '??????????': answer.answer
                        }
                        listAnswers.append(data)
                    df3 = pd.DataFrame(listAnswers)

                    countAnswer = countAnswers(get_answer, test.id, 'test')

                    df4 = pd.DataFrame(countAnswer)
                    name_short = "".join(random.choice(string.ascii_letters) for j in range(random.randint(1, 10)))

                    name = f'{name_short}.xlsx'
                    writer = pd.ExcelWriter(MEDIA_ROOT + '/file_excel/' + name, engine='xlsxwriter')
                    df3.to_excel(writer, sheet_name='?????????? ???? ??????????????')
                    df4.to_excel(writer, sheet_name='???????????????????? ??????????????')
                    writer.save()

                    return Response({'link': 'http://31.31.202.177:8000/media/file_excel/' + name})
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
            if request.data['type'] == 'copy':
                poll_copy = Polls(category=poll.category,
                                  datePosting=datetime.now(),
                                  description=poll.description,
                                  in_archive=False,
                                  latePosting=True,
                                  points=poll.points,
                                  session_id=SessionTC.objects.get(active_session=True).number_session,
                                  title=poll.title)
                poll_copy.save()
                questions = Questions.objects.filter(poll_id=poll.id)
                for question in questions:
                    question_copy = Questions(question=question.question,
                                              answer=question.answer,
                                              poll_id=poll_copy.id)
                    question_copy.save()

            if request.data['type'] == 'report':
                get_answer = QuestionsCheck.objects.filter(poll_id=poll.id)
                listAnswers = []
                for answer in get_answer:
                    data = {
                        '??????': answer.user_valuer.first_name + ' ' + answer.user_valuer.last_name,
                        '????????????': answer.question.question,
                        '??????????': answer.answer
                    }
                    listAnswers.append(data)
                df3 = pd.DataFrame(listAnswers)

                countAnswer = countAnswers(get_answer, poll.id, 'poll')

                df4 = pd.DataFrame(countAnswer)
                name_short = "".join(random.choice(string.ascii_letters) for j in range(random.randint(1, 10)))

                name = f'{name_short}.xlsx'
                writer = pd.ExcelWriter(MEDIA_ROOT + '/file_excel/' + name, engine='xlsxwriter')

                df3.to_excel(writer, sheet_name='?????????? ???? ??????????????')
                df4.to_excel(writer, sheet_name='???????????????????? ??????????????')

                writer.save()

                return Response({'link': 'http://31.31.202.177:8000/media/file_excel/' + name})

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
                poll.datePosting = datetime.now()
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
        global check_completed, active_test, list_questions, active_poll_team
        if request.query_params.__len__() == 1:
            category = 'participant'
        else:
            category = request.query_params['type']
        active_session = SessionTC.objects.get(active_session=True).number_session

        if category == 'participant':
            active_poll_team = Polls.objects.get(session_id=active_session, latePosting=False, in_archive=False,
                                                 category=category)
            check_completed = PollsCheck.objects.filter(poll_id=active_poll_team.id,
                                                        poll_user_id=request.query_params['id'],
                                                        user_valuer_id=request.user.profile.id).exists()
        else:
            if category == 'test':
                active_test = Test.objects.get(session_id=active_session,
                                               in_archive=False,
                                               latePosting=False,
                                               id=request.query_params['id'])
                check_completed = CheckTest.objects.filter(test_id=active_test.id,
                                                           user=request.user.profile.id).exists()
            else:
                active_poll_team = Polls.objects.get(session_id=active_session, in_archive=False, category=category,
                                                     id=request.query_params['id'])
                check_completed = PollsCheck.objects.filter(poll_id=active_poll_team.id,
                                                            user_valuer_id=request.user.profile.id).exists()
        if check_completed:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            if category == 'test':
                serializer = TestSerializer(active_test).data
                queryset = QuestionsTest.objects.filter(test_id=active_test.id)
                list_questions = []
                for el in queryset:
                    queryset_answers = AnswersTest.objects.filter(question_id=el.id)
                    answer = []
                    for i in queryset_answers:
                        answer.append(i.answer)
                    list_questions.append({'question': el.question, 'answer': answer, 'id': el.id})
                data = {'poll_info': serializer, 'questions': list_questions, 'type': 'test'}

            else:
                serializer = PollsSerializer(active_poll_team).data
                queryset = Questions.objects.filter(poll_id=active_poll_team.id)
                list_questions = []

                i = 0
                for item in queryset:
                    question = item.question
                    answer = item.answer.split('|')
                    if item.poll.category != 'participant':
                        del answer[0]
                    else:
                        for i in range(int(answer[0]) + 1):
                            if i == 0:
                                answer.clear()
                            answer.append(i)
                    i += 1
                    list_questions.append(
                        {'question': question, 'answer': answer, 'id': i, 'freeAnswer': item.freeAnswer})

                data = {'poll_info': serializer, 'questions': list_questions, 'type': 'other'}

            return Response(data)


class CheckPollTeam(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            type = request.data['type']
        except KeyError:
            type = None
        if type == 'other' or type == 'test':
            save_poll(request.data)
            return Response(status=status.HTTP_200_OK)
        else:
            poll = PollsCheck(poll_id=request.data['id_poll'], user_valuer_id=request.data['user_id'],
                              poll_user_id=request.data['user_poll_id'])
            poll.save()

            for el in request.data['answers']:
                get_id_question = Questions.objects.get(question=el, poll_id=request.data['id_poll']).id
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

        """???????????????????? ???? ????????????????????"""
        list_category = ['service', 'spiker', 'other', 'test']
        data = dict.fromkeys(list_category)
        for i in list_category:

            polls = get_all_polls.filter(category=i, in_archive=False, latePosting=False,
                                         session_id=Profile.objects.get(id=user_id).session_id)
            serializer = PollsSerializer(polls, many=True).data
            if polls.count() == 0:
                continue
            else:
                data[i] = serializer
        get_test = Test.objects.filter(session_id=Profile.objects.get(id=user_id).session_id, latePosting=False,
                                       in_archive=False)
        get_check_test = CheckTest.objects.filter(user_id=user_id)
        for el in get_check_test:
            get_test = get_test.exclude(id=el.test_id)
        serializer = TestSerializer(get_test, many=True).data
        if get_test.count() != 0:
            data['test'] = serializer

        return Response(data)


class GetAnalytics(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """?????????????????? ???????????? ???? ??????????????"""
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

        """?????????????????? ???????????? ???? ???????????????? ????????????????????"""
        rating = Rating.objects.all()
        rating_list = []
        for el in rating:
            user = Profile.objects.get(username=el.username).first_name + ' ' + \
                   Profile.objects.get(username=el.username).last_name

            data = {'rating': el.rating, 'points': el.points, 'user': user, 'team': el.username.profile.team_id,
                    'session': el.username.profile.session.number_session}

            rating_list.append(data)

        """?????????????????? ???????????????????? ?????????????? ?? ??????????????"""
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
        """?????????????????? ???????????? ???? ???????????????? ????????????????????"""
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
        """?????????????????? ???????????? ???? ???????????????? ????????????"""
        all_users = Rating.objects.all()
        rating_list = []
        i = 1
        for el in all_users:
            if el.username.profile.session_id == int(request.query_params.__getitem__('session')):
                if el.username.profile.team_id == '?????????????? ' + request.query_params.__getitem__('team'):
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
        """???????????????????? ?????????? ???? ??????????????????"""
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

        if request.query_params['type'] == 'excel_test':
            users = Profile.objects.all()
            list_elements_table = []
            for profile in users:
                fio = profile.first_name + ' ' + profile.last_name
                list_competition = [1, 2, 3, 4]
                data = {'fio': fio,
                        'to1': None, 'after1': None, 'difference1': None,
                        'to2': None, 'after2': None, 'difference2': None,
                        'to3': None, 'after3': None, 'difference3': None,
                        'to4': None, 'after4': None, 'difference4': None}
                for el in list_competition:
                    tests = list(Test.objects.filter(num_comp_id=el))
                    if tests.__len__() == 2:
                        first_test = tests[0].id
                        second_test = tests[1].id
                        get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                            poll_id=first_test)
                        summ = 0
                        for j in get_summ_points:
                            summ += j.point
                        data[('to' + str(el))] = summ

                        get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                            poll_id=second_test)
                        summ = 0
                        for j in get_summ_points:
                            summ += j.point
                        data[('after' + str(el))] = summ
                        data[('difference' + str(el))] = data.get('to' + str(el)) - data.get('after' + str(el))
                    elif tests.__len__() == 0:
                        data[('to' + str(el))] = 0
                        data[('after' + str(el))] = 0
                        data[('difference' + str(el))] = 0
                    else:
                        first_test = tests[0].id
                        get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                            poll_id=first_test)
                        summ = 0
                        for j in get_summ_points:
                            summ += j.point
                        data[('to' + str(el))] = summ
                        data[('after' + str(el))] = 0
                        data[('difference' + str(el))] = data.get('to' + str(el)) - data.get('after' + str(el))

                list_elements_table.append(data)
            serializer = list_elements_table
            file = 'Test_'

        df = pd.DataFrame(serializer)
        name = file + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + '.xlsx'
        df.to_excel(MEDIA_ROOT + '/file_excel/' + name)

        return Response({'url': '/images/media/file_excel/' + name})


class UploadUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        """???????????????? ???????? ?????? ???????????????? ???? ????(?????????????? ?????????????????? ?????????????????????? ????????)"""
        file = FileUpload.objects.all().order_by('-id')[:1][0]
        exel_data_df = pandas.read_excel(file.file.path)
        for index, row in exel_data_df.iterrows():
            if row['email'] != '' or None:
                password = ''
                for x in range(8):
                    password = password + random.choice(
                        list('1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))

                if User.objects.filter(username=str(row['email']).split('@')[0]).exists():
                    continue
                serializer = UserSerializerWithToken(
                    data={'username': str(row['email']).split('@')[0], 'password': password, 'email': row['email']})

                """CREATE COUNTRY"""
                if Country.objects.filter(country=row['??????????']).count() == 0:
                    Country(country=row['??????????']).save()

                if serializer.is_valid():
                    serializer.save()
                    a = User.objects.get(username=str(row['email']).split('@')[0])
                    a.email = str(row['email'])
                    a.save()
                    create_info_for_user = Profile(
                        first_name=row['??????'],
                        last_name=row['??????????????'],
                        country_id=row['??????????'],
                        team_id=row['??????????????'],
                        birthday=row['???????? ????????????????'],
                        username_id=str(row['email']).split('@')[0],
                        session_id=row['??????????']
                    ).save()
                    create_permission_for_user = PermissionUser(
                        permission_id='Participant',
                        username_id=str(row['email']).split('@')[0]).save()
                    create_rating_field = Rating(username_id=str(row['email']).split('@')[0],
                                                 rating=Profile.objects.exclude(team='Staff').count(), points=0).save()

        return Response(status=status.HTTP_202_ACCEPTED)


class CreateTest(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
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


class GetTests(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        team = Team.objects.get(id=request.query_params.__getitem__('team'))
        users = Profile.objects.filter(session_id=int(request.query_params.__getitem__('session')),
                                       team_id=team.name)
        list_elements_table = []
        list_rating_users = []
        for profile in users:
            fio = profile.first_name + ' ' + profile.last_name
            list_competition = [1, 2, 3, 4]
            data = {'fio': fio,
                    'to1': None, 'after1': None, 'difference1': None,
                    'to2': None, 'after2': None, 'difference2': None,
                    'to3': None, 'after3': None, 'difference3': None,
                    'to4': None, 'after4': None, 'difference4': None}
            for el in list_competition:
                tests = list(
                    Test.objects.filter(num_comp_id=el, session_id=int(request.query_params.__getitem__('session'))))
                if tests.__len__() == 2:
                    first_test = tests[0].id
                    second_test = tests[1].id
                    get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                        poll_id=first_test)
                    summ = 0
                    for j in get_summ_points:
                        summ += j.point
                    data[('to' + str(el))] = summ

                    get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                        poll_id=second_test)
                    summ = 0
                    for j in get_summ_points:
                        summ += j.point
                    data[('after' + str(el))] = summ
                    data[('difference' + str(el))] = data.get('after' + str(el)) - data.get('to' + str(el))
                elif tests.__len__() == 0:
                    data[('to' + str(el))] = 0
                    data[('after' + str(el))] = 0
                    data[('difference' + str(el))] = 0
                else:
                    first_test = tests[0].id
                    get_summ_points = QuestionsCheckTest.objects.filter(user_valuer_id=profile.id,
                                                                        poll_id=first_test)
                    summ = 0
                    for j in get_summ_points:
                        summ += j.point
                    data[('to' + str(el))] = summ
                    data[('after' + str(el))] = 0
                    data[('difference' + str(el))] = data.get('after' + str(el)) - data.get('to' + str(el))

            list_elements_table.append(data)

            """"?????????????????? ???????????? ???? ????????????????????"""
            rating_data = Rating.objects.get(username_id=profile.username)
            data_user = {'fio': profile.first_name + ' ' + profile.last_name,
                         'num': rating_data.rating,
                         'points': rating_data.points,
                         'team': profile.team_id,
                         'session': profile.session_id}
            list_rating_users.append(data_user)
        list_rating_users = sorted(list_rating_users, key=lambda k: k['num'])
        """?????????????? ???????????? ?? ????????????"""
        rating_team = RatingTeam.objects.filter(session_id=int(request.query_params.__getitem__('session'))).order_by(
            'rating')
        i = 1
        list_rating_team = []
        for team in rating_team:
            data_team = {
                'num': i,
                'team': team.team.name,
                'session': team.session_id,
                'points': team.points
            }
            list_rating_team.append(data_team)
            i += 1

        df = pd.DataFrame(list_elements_table)
        df2 = pd.DataFrame(list_rating_users)
        df3 = pd.DataFrame(list_rating_team)
        name = '??????????.xlsx'
        writer = pd.ExcelWriter(MEDIA_ROOT + '/file_excel/' + name, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='test')
        df2.to_excel(writer, sheet_name='rating_user')
        df3.to_excel(writer, sheet_name='rating_team')
        writer.save()

        return Response({'test': list_elements_table, 'users': list_rating_users, 'team': list_rating_team,
                         'link': 'http://31.31.202.177:8000/media/file_excel/' + name})


"""?????????????????? ?????????? ????????????"""


class AnaliticNew(APIView):
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    @staticmethod
    def get(request):
        """???????? ???????????? ?????? ?????????????? (?????????????? 1 ?? ???????????? ????????????????)"""
        queryset_logger = LogPoint.objects.all()
        logger_list = []
        if queryset_logger.count() != 0:
            for log in queryset_logger:
                log_data = {
                    'fio': log.username,
                    'points': log.points,
                    'date': (log.date + timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'),
                    'polls_test': log.poll
                }
                logger_list.append(log_data)
        """???????? ???????????? ?????? ???????????????? ???????? ???????????????????? (?????????????? 2 ?? ???????????? ????????????????)"""
        queryset_rating_all_users = Rating.objects.all().order_by('rating')
        rating_user = []
        if queryset_rating_all_users.count() != 0:
            for user in queryset_rating_all_users:
                rating_user_data = {
                    'num': user.rating,
                    'fio': user.username.profile.first_name + ' ' + user.username.profile.last_name,
                    'points': user.points,
                    'team': user.username.profile.team_id,
                    'session': user.username.profile.session_id
                }
                rating_user.append(rating_user_data)
        df = pd.DataFrame(rating_user)

        """???????? ???????????? ?????? ???????????????? ???????? ???????????? (?????????????? 3 ?? ???????????? ????????????????)"""
        queryset_rating_all_teams = RatingTeam.objects.all().order_by('rating')
        rating_team = []
        if queryset_rating_all_teams.count() != 0:
            for team in queryset_rating_all_teams:
                rating_team_data = {
                    'num': team.rating,
                    'team': team.team_id,
                    'session': team.session_id,
                    'points': team.points
                }
                rating_team.append(rating_team_data)

        df2 = pd.DataFrame(rating_team)
        df3 = pd.DataFrame(logger_list)
        name = '??????????J.xlsx'
        writer = pd.ExcelWriter(MEDIA_ROOT + '/file_excel/' + name, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='rating_team')
        df2.to_excel(writer, sheet_name='rating_user')
        df3.to_excel(writer, sheet_name='logger')
        writer.save()

        data = {'logger': logger_list, 'rating_user': rating_user, 'rating_team': rating_team,
                'link': 'http://31.31.202.177:8000/media/file_excel/' + name}
        return Response(data)


def CreateStartInfo(response):
    """???????????????????? ????????"""
    try:
        SessionTC(number_session=0, name_session='?????????? ??????????????????', active_session=None).save()
    except:
        pass
    try:
        SessionTC(number_session=1, name_session='?????????? 1', active_session=True).save()
    except:
        pass
    try:
        SessionTC(number_session=2, name_session='?????????? 2', active_session=False).save()
    except:
        pass
    try:
        SessionTC(number_session=3, name_session='?????????? 3', active_session=False).save()
    except:
        pass
    try:
        SessionTC(number_session=4, name_session='?????????? 4', active_session=False).save()
    except:
        pass
    try:
        SessionTC(number_session=5, name_session='?????????? 5', active_session=False).save()
    except:
        pass

    """???????????????????? ????????????"""
    i = 0
    while i < 56:
        if Team.objects.filter(name='?????????????? ' + str(i)).count() == 0:
            if i == 0:
                Team(name='Staff').save()
            else:
                team = Team(name='?????????????? ' + str(i))
                team.save()
                for session in SessionTC.objects.all().exclude(number_session=0):
                    RatingTeam(team=team, session=session).save()
            i += 1
        else:
            i += 1

    return HttpResponse("Here's the text of the Web page.")


class GetUsersInfo(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        profile = Profile.objects.get(username=User.objects.get(username=request.query_params.__getitem__('username')))
        list_polls = []
        list_test = []
        i = 1
        for el in PollsCheck.objects.filter(user_valuer_id=profile.username.id):
            list_polls.append({'num': i, 'name': el.poll.title})
            i += 1
        j = 1
        for el in CheckTest.objects.filter(user_id=profile.username.id):
            list_test.append({'num': j, 'name': el.test.title})
            j += 1
        try:
            data = {'FirstLastName': profile.first_name + ' ' + profile.last_name,
                    'username': str(profile.username),
                    'birthday': profile.birthday.strftime('%Y-%m-%d'),
                    'dataJoin': (profile.username.date_joined + timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'),
                    'country': str(profile.country),
                    'team': str(profile.team),
                    'session': str(profile.session),
                    'points': str(Rating.objects.get(username_id=profile.username).points),
                    'name_polls': list_polls,
                    'name_test': list_test}
        except:
            data = {'FirstLastName': profile.first_name + ' ' + profile.last_name,
                    'username': str(profile.username),
                    'birthday': profile.birthday.strftime('%Y-%m-%d'),
                    'dataJoin': (profile.username.date_joined + timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'),
                    'country': str(profile.country),
                    'team': str(profile.team),
                    'session': str(profile.session),
                    'points': '???? ??????????????????????????!',
                    'name_polls': list_polls,
                    'name_test': list_test}

        return Response(data)


class PullPoints(APIView):
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    @staticmethod
    def get(request):
        pull_points = int(request.query_params.__getitem__('points'))
        username = request.query_params.__getitem__('username')

        rating_points = Rating.objects.get(username=username)
        rating_points.points += pull_points
        rating_points.save()

        rating_team = RatingTeam.objects.get(team_id=rating_points.username.profile.team.name,
                                             session_id=rating_points.username.profile.session_id)
        rating_team.points += pull_points
        rating_team.save()

        return Response({'points': rating_points.points})


class SearchUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def get(request):
        name = request.query_params.__getitem__('value')
        name = name.split(' ')
        if name.__len__() > 1:
            get_users = Profile.objects.filter(last_name=name[0].title())
            if get_users.count() == 0:
                get_users = Profile.objects.filter(first_name=name[0].title(), last_name=name[1].title())
            else:
                get_users = Profile.objects.filter(first_name=name[1].title(), last_name=name[0].title())
        else:
            get_users = Profile.objects.filter(last_name=name[0].title())
            if get_users.count() == 0:
                get_users = Profile.objects.filter(first_name=name[0].title())

        data = []
        for username in get_users:
            dict_user = {}
            user_info = Profile.objects.get(username_id=username.username)
            user_permission = PermissionUser.objects.get(username_id=username.username)

            dict_user = {
                'username': str(username.username),
                'first_name': user_info.first_name,
                'last_name': user_info.last_name,
                'birthday': str(user_info.birthday),
                'country': user_info.country_id,
                'team': user_info.team_id,
                'permission': user_permission.permission.name
            }

            data.append(dict_user)
        return Response(data)


class SendNewPass(APIView):
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser,)

    @staticmethod
    def get(request):
        username = request.query_params.__getitem__('value')

        get_email_user = User.objects.get(username=username)
        password = ''
        for x in range(8):
            password = password + random.choice(
                list('1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))
        get_email_user.set_password(password)
        get_email_user.save()

        """???????????????? ???????????? ?? ?????????????? ?????? ??????????"""

        message = MIMEMultipart()
        message['Subject'] = '?????????????????? ?????? ?????????? ?? ?????????????? ?????????????? ????'
        message['From'] = 'master@tspolls.ru'
        message['To'] = get_email_user.email
        message['BCC'] = 'mkovalevhse@yandex.ru'

        html = """\
                                <html>
                                    <head></head>
                                    <body>
                                    <h4>?????????? ???????????????????? ???? ?????????????????????? ??????????????. ?????????? ??????????!</h4>

                                    <p>???? ?????????? ?????????????? ??????????????????????. ???? ???????? ???????????? ???? ?????????????? ?????????????????????? ?? 
                                    ???????????????????? ?????????? ?????????????? #????????????????????. ???????????????? ?????????????????? ?????????????????? ???????????????? 
                                    ?????????????????? ????????????. ?????????? ???? ?????????????? ?????????????????? ???????????????? ?????????????????? ??????????????????, 
                                    ?????????????????? ????????????, ???????????? ???????????????????? ?? ???????? ????????. ?????????????????? ?????????????? ???????????????? ?????????? 
                                    ??????????????????????, ???????????????? ????????????. ?????? ???????? ?????????????????????? ?????????????????? ???????????? 
                                    ??????????.</p><br> <p>???????? ?? ???????????????????? ?????????????????? ????????????????, ???????????? ?????????? ???????????? 
                                    ??????????????????: postmaster@tspolls.ru</p><br> 


                                    <p>?????????? ?? ???????????? ???? ?????????????? ????????. ???? ????????????????????????, ???????????????????? ???? ???????????? ????????????.</p><br>


                                    <span><b>Login:</b>  """ + get_email_user.email.split('@')[0] + """</span><br>
                                    <span><b>Password:</b>  """ + password + """</span><br>
                                    <a href='http://tspolls.ru/'>????????????????????????????</a>
                                    </body></html>"""

        text = MIMEText(html, 'html')
        message.attach(text)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP('mail.nic.ru', 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            try:
                server.login('master@tspolls.ru', '124578QWas')
                server.sendmail(message['From'], message['To'], message.as_string())
                server.quit()
            except:
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response(status=status.HTTP_200_OK)


class Edit(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            competention = request.data['comp']
            test = Test.objects.get(id=request.data['id'])
            test.title = request.data['title']
            test.description = request.data['description']
            test.points = request.data['points']
            test.session_id = request.data['session']
            test.num_comp_id = competention
            test.save()
            return Response(status=status.HTTP_200_OK)
        except KeyError:
            poll = Polls.objects.get(id=request.data['id'])
            poll.title = request.data['title']
            poll.description = request.data['description']
            poll.points = request.data['points']
            poll.session_id = request.data['session']
            poll.save()
            return Response(status=status.HTTP_200_OK)


class DelUsers(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def get(request):
        get_user_session = Profile.objects.filter(session_id=5)

        for user in get_user_session:
            us = User.objects.get(username=user.username)
            print(us.username)
            us.delete()
        return Response('success')


class PostPassword(APIView):
    permission_classes = (permissions.AllowAny,)

    @staticmethod
    def post(request):
        try:
            get_email_user = User.objects.get(email=request.data.get('email'))
        except:
            return Response('???????????????????????? ?? ?????????? ?????????????????????? ???????????? ???? ????????????????????!'
                            '???????????????????? ?? ?????????????????????????????? ??????????????: tspolls2021@gmail.com',
                            status=status.HTTP_404_NOT_FOUND)
        password = ''
        for x in range(8):
            password = password + random.choice(
                list('1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))
        get_email_user.set_password(password)

        """???????????????? ???????????? ?? ?????????????? ?????? ??????????"""
        smtp_data = SmtpServer.objects.order_by('-created_date').first()

        message = MIMEMultipart()
        message['Subject'] = '?????????????????? ?????? ?????????? ?? ?????????????? ?????????????? ????'
        message['From'] = 'master@tspolls.ru'
        message['To'] = get_email_user.email

        html = """\
                                        <html>
                                            <head></head>
                                            <body>
                                            <h4>?????????? ???????????????????? ???? ?????????????????????? ??????????????. ?????????? ??????????!</h4>

                                    <p>???? ?????????? ?????????????? ??????????????????????. ???? ???????? ???????????? ???? ?????????????? ?????????????????????? ?? 
                                    ???????????????????? ?????????? ?????????????? #????????????????????. ???????????????? ?????????????????? ?????????????????? ???????????????? 
                                    ?????????????????? ????????????. ?????????? ???? ?????????????? ?????????????????? ???????????????? ?????????????????? ??????????????????, 
                                    ?????????????????? ????????????, ???????????? ???????????????????? ?? ???????? ????????. ?????????????????? ?????????????? ???????????????? ?????????? 
                                    ??????????????????????, ???????????????? ????????????. ?????? ???????? ?????????????????????? ?????????????????? ???????????? 
                                    ??????????.</p><br> <p>???????? ?? ???????????????????? ?????????????????? ????????????????, ???????????? ?????????? ???????????? 
                                    ??????????????????: postmaster@tspolls.ru</p><br> 


                                            <p>?????????? ?? ???????????? ???? ?????????????? ????????. ???? ????????????????????????, ???????????????????? ???? ???????????? ????????????.</p><br>


                                            <span><b>Login:</b>  """ + get_email_user.email.split('@')[0] + """</span><br>
                                            <span><b>Password:</b>  """ + password + """</span><br>
                                            <a href='http://tspolls.ru/'>????????????????????????????</a>
                                            </body></html>"""

        text = MIMEText(html, 'html')
        message.attach(text)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP('mail.nic.ru', 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            try:
                server.login('master@tspolls.ru', '124578QWas')
                server.sendmail(message['From'], message['To'], message.as_string())
                server.quit()
                get_email_user.save()
            except Exception as e:
                return Response(f"???? ?????????????? ?????????????????? ????????????, ???????????????????? ??????????!({str(e)})",
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response("???????????? ?????????????? ??????????????????!", status=status.HTTP_202_ACCEPTED)
