import logging

from rest_framework import status

from model.models import Polls, Questions


def save_poll_participant(request):

    if Polls.objects.filter(in_archive=False, category='participant').exists():
        set_archive = Polls.objects.get(in_archive=False, category='participant')
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
              datePosting=request['values']['datePosting']).save()
    else:
        Polls(title=request['values']['title'],
              description=request['values']['description'],
              points=request['values']['points'],
              category=request['values']['category']).save()


def save_question_and_answer(request, answer, question):
    Questions(poll_id=Polls.objects.get(title=request['info']['values']['title'],
                                        description=request['info']['values']['description']).id,
              question=question,
              answer=answer).save()
