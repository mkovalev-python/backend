import logging

from rest_framework import status

from model.models import Polls, Questions, Rating, Profile, PollsCheck, QuestionsCheck, Team


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
            str_answer += ' ' + answer['answer']

        save_question_and_answer(request, str_answer, question['question'])

    return status.HTTP_201_CREATED


def general_save(request):
    if request['latePosting']:
        Polls(title=request['values']['title'],
              description=request['values']['description'],
              category=request['values']['category'],
              points=request['values']['points'],
              latePosting=request['latePosting'],
              datePosting=request['values']['datePosting'],
              session_id=request['values']['session']).save()
    else:
        Polls(title=request['values']['title'],
              description=request['values']['description'],
              points=request['values']['points'],
              category=request['values']['category'],
              session_id=request['values']['session']).save()


def save_question_and_answer(request, answer, question):
    Questions(poll_id=Polls.objects.get(title=request['info']['values']['title'],
                                        description=request['info']['values']['description']).id,
              question=question,
              answer=answer).save()


def rating():
    sort_table = Rating.objects.order_by('-points')

    i = 1

    for user in sort_table:
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

    points = int(s_points/n_users)

    save_points = Rating.objects.get(username_id=user.username_id)
    save_points.points += points
    save_points.save()


def save_poll(params):
    PollsCheck(poll_id=params['id_poll'], user_valuer_id=params['user_id']).save()

    for el in params['answers']:
        get_id_question = Questions.objects.get(question=el).id
        QuestionsCheck(poll_id=params['id_poll'],
                       user_valuer_id=params['user_id'],
                       answer=params['answers'][el],
                       question_id=get_id_question).save()

    add_points_for_user = Rating.objects.get(
        username_id=Profile.objects.get(id=params['user_id']).username_id)
    add_points_for_user.points += Polls.objects.get(id=params['id_poll']).points
    add_points_for_user.save()


def get_points(poll):
    get_team_id = Team.objects.exclude(name='Staff')

    for team in get_team_id:
        for user in Profile.objects.filter(team_id=team):
            bool_polls = PollsCheck.objects.filter(poll_user_id=user.id).exists()
            if bool_polls:
                get_all_check_polls_for_user = PollsCheck.objects.filter(poll_id=poll.id,poll_user_id=user.id)
                summ_points = 0
                for polls in get_all_check_polls_for_user:
                    get_all_questions_check = QuestionsCheck.objects.filter(poll_check_id=polls.id)
                    for answer in get_all_questions_check:
                        summ_points += int(answer.answer)
                points_my_team(team, poll, summ_points, user)
            else:
                continue

