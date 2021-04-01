import logging

from rest_framework import status

from model.models import Polls, Questions, Rating


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
