from datetime import datetime

from rest_framework import status

from model.models import Polls, Questions, Rating, Profile, PollsCheck, QuestionsCheck, Team, LogPoint, RatingTeam, \
    CheckTest, QuestionsCheckTest, QuestionsTest, Test, AnswersTest


def save_poll_participant(request):
    if not request['info']['latePosting']:
        if Polls.objects.filter(in_archive=False, category='participant', latePosting=False).exists():
            set_archive = Polls.objects.get(in_archive=False, latePosting=False, category='participant')
            set_archive.in_archive = True
            set_archive.save()

    general_save(request['info'])

    for question in request['questions']:
        save_question_and_answer(request, question['answer'], question['question'])

    return status.HTTP_201_CREATED


def save_poll_all(request):
    general_save(request['info'])

    for question in request['questions']:
        str_answer = ''
        for answer in question['answers']:
            str_answer += '|' + answer['answer']
        try:
            freeAnswer = question['freeAnswer']
        except KeyError:
            freeAnswer = False
        save_question_and_answer(request, str_answer, question['question'], freeAnswer)

    return status.HTTP_201_CREATED


def general_save(request):
    if request['latePosting']:
        Polls(title=request['values']['title'],
              description=request['values']['description'],
              category=request['values']['category'],
              points=request['values']['points'],
              latePosting=request['latePosting'],
              session_id=request['values']['session']).save()
    else:
        Polls(title=request['values']['title'],
              description=request['values']['description'],
              points=request['values']['points'],
              category=request['values']['category'],
              session_id=request['values']['session']).save()


def save_question_and_answer(request, answer, question, freeAnswer=None):
    Questions(poll_id=Polls.objects.get(title=request['info']['values']['title'],
                                        description=request['info']['values']['description']).id,
              question=question,
              answer=answer,
              freeAnswer=freeAnswer).save()


def rating():
    sort_table = Rating.objects.order_by('-points')
    sort_table_team = RatingTeam.objects.order_by('-points')

    i = 1

    for user in sort_table:
        user.rating = i
        user.save()
        i += 1

    i = 1

    for user in sort_table_team:
        user.rating = i
        user.save()
        i += 1


def points_my_team(team, poll, s_points, user):
    team_count = Profile.objects.exclude(username_id=user.username_id).filter(team_id=team, session_id=poll.session_id)
    null_users = 0
    for el in team_count:
        if PollsCheck.objects.filter(user_valuer_id=el.id, poll_id=poll.id, poll_user_id=user.id).exists():
            continue
        else:
            null_users += 1

    n_users = team_count.count() - null_users
    try:
        points = int(s_points / n_users)
    except:
        points = 0

    save_points = Rating.objects.get(username_id=user.username_id)
    save_points.points += points
    save_points.save()
    log_point(points, poll.id, user.id, True, None)


def save_poll(params):
    if params['type'] == 'test':
        test = CheckTest(test_id=params['id_poll'], user_id=int(params['user_id']))
        test.save()

        for el in params['answers']:
            get_id_question = QuestionsTest.objects.get(question=el, test_id=params['id_poll']).id
            QuestionsCheckTest(poll_id=params['id_poll'],
                               user_valuer_id=params['user_id'],
                               answer=params['answers'][el],
                               question_id=get_id_question,
                               poll_check_id=test.id,
                               point=AnswersTest.objects.get(question_id=get_id_question,
                                                             answer=params['answers'][el]).points).save()

        add_points_for_user = Rating.objects.get(
            username_id=Profile.objects.get(id=params['user_id']).username_id)
        add_points_for_user.points += Test.objects.get(id=params['id_poll']).points
        add_points_for_user.save()
        log_point(Test.objects.get(id=params['id_poll']).points, params['id_poll'], params['user_id'], True, 'test')
        """???????????????????????? ???????????????? ??????????????"""
        get_user = Profile.objects.get(id=params['user_id'])
        add_point_team = RatingTeam.objects.get(team_id=get_user.team_id, session_id=get_user.session_id)
        add_point_team.points += test.test.points
        add_point_team.save()

    else:
        poll = PollsCheck(poll_id=params['id_poll'], user_valuer_id=params['user_id'])
        poll.save()

        for el in params['answers']:
            get_id_question = Questions.objects.get(question=el, poll_id=params['id_poll']).id
            QuestionsCheck(poll_id=params['id_poll'],
                           user_valuer_id=params['user_id'],
                           answer=params['answers'][el],
                           question_id=get_id_question,
                           poll_check_id=poll.id).save()

        add_points_for_user = Rating.objects.get(
            username_id=Profile.objects.get(id=params['user_id']).username_id)
        add_points_for_user.points += Polls.objects.get(id=params['id_poll']).points
        add_points_for_user.save()
        log_point(Polls.objects.get(id=params['id_poll']).points, params['id_poll'], params['user_id'], True, None)
        """???????????????????????? ???????????????? ??????????????"""
        get_user = Profile.objects.get(id=params['user_id'])
        add_point_team = RatingTeam.objects.get(team_id=get_user.team_id, session_id=get_user.session_id)
        add_point_team.points += poll.poll.points
        add_point_team.save()


def get_points(poll):
    get_team_id = Team.objects.exclude(name='Staff')

    for team in get_team_id:
        for user in Profile.objects.filter(team_id=team):
            bool_polls = PollsCheck.objects.filter(poll_user_id=user.id).exists()
            if bool_polls:
                get_all_check_polls_for_user = PollsCheck.objects.filter(poll_id=poll.id, poll_user_id=user.id)
                summ_points = 0
                for polls in get_all_check_polls_for_user:
                    get_all_questions_check = QuestionsCheck.objects.filter(poll_check_id=polls.id)
                    for answer in get_all_questions_check:
                        summ_points += int(answer.answer)
                points_my_team(team, poll, summ_points, user)
            else:
                continue


def add_points(req, poll):
    get_user = Profile.objects.get(id=req.data['user_id'])
    team_count = Profile.objects.exclude(username_id=get_user.username_id).filter(team_id=get_user.team_id).count()
    cheking_pollscheck = PollsCheck.objects.filter(user_valuer_id=get_user.id, poll_id=poll.poll_id).count()
    if team_count == cheking_pollscheck:
        add_p = Rating.objects.get(username_id=get_user.username_id)
        add_p.points += poll.poll.points
        add_p.save()
        log_point(poll.poll.points, poll.poll.id, get_user.id, True, None)
        """???????????????????????? ???????????????? ??????????????"""
        add_point_team = RatingTeam.objects.get(team_id=get_user.team_id, session_id=get_user.session_id)
        add_point_team.points += poll.poll.points
        add_point_team.save()


def log_point(points, poll_id, user_id, bool_add, type):
    """?????????????? ???????????????????????? ????????????"""
    if type == 'test':
        poll = Test.objects.get(id=poll_id).title
    else:
        poll = Polls.objects.get(id=poll_id).title
    user = Profile.objects.get(id=user_id)
    LogPoint(points=points, date=datetime.now(), add=bool_add, poll=poll, username=user.first_name
                                                                                   + ' ' +
                                                                                   user.last_name).save()
    return print('?????????? ????????????????????????')


def countAnswers(answers, id, test_or_poll):
    if test_or_poll == 'poll':
        get_questions = Questions.objects.filter(poll_id=id)
        dict_questions = {}
        for question in get_questions:
            dict_answers = {}
            a = question.answer.split('|')
            if a.__len__() == 1:
                answersss = a
            else:
                answersss = a[1:]
            for answer in answersss:
                dict_answers[answer] = 0
            if question.freeAnswer:
                dict_answers['???????? ??????????????'] = 0
            dict_questions[question.question] = dict_answers

        for answer in answers:
            try:
                dict_questions[answer.question.question][answer.answer] += 1
            except KeyError:
                dict_questions[answer.question.question]['???????? ??????????????'] += 1

    else:
        get_questions = QuestionsTest.objects.filter(test_id=id)
        dict_questions = {}
        for question in get_questions:
            answerss = AnswersTest.objects.filter(question_id=question.id)
            dict_answers = {}
            for answer in answerss:
                dict_answers[answer.answer] = 0
            dict_questions[question.question] = dict_answers

        for answer in answers:
            dict_questions[answer.question.question][answer.answer] += 1

    return dict_questions
