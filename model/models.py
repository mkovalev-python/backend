from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class Profile(models.Model):
    """Модель пользователя"""

    username = models.OneToOneField(User, on_delete=models.CASCADE, to_field='username', verbose_name='Логин '
                                                                                                      'пользователя')
    first_name = models.CharField('Имя', max_length=100, null=False)
    last_name = models.CharField('Фамилия', max_length=100, null=False)
    country = models.ForeignKey('Country', on_delete=models.CASCADE, null=False, to_field='country')
    birthday = models.DateField('Дата рождения', null=False)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, to_field='name', verbose_name='Команда')
    avatar = models.ImageField('Аватар', upload_to='avatar/', default='avatar/josh-d-avatar.jpg')
    session = models.ForeignKey('SessionTC', on_delete=models.CASCADE, to_field='number_session', null=True)

    def __str__(self):
        return str(self.username)

    class Meta:
        verbose_name = 'Данные пользователя'
        verbose_name_plural = 'Данные пользователя'


class Country(models.Model):
    """Модель городов России"""

    country = models.CharField('Город', max_length=500, unique=True)

    def __str__(self):
        return self.country

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class Team(models.Model):
    """Модель команд"""

    name = models.CharField('Название команды', unique=True, max_length=500)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'


class PermissionUser(models.Model):
    """Модель ролей у пользователя системы"""

    username = models.OneToOneField(User, on_delete=models.CASCADE, to_field='username')
    permission = models.ForeignKey('Permission', on_delete=models.CASCADE, to_field='slug')

    def __str__(self):
        return str(self.username)

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователя'


class Permission(models.Model):
    """Модель ролей системы"""

    name = models.CharField('Роли', unique=True, max_length=500)
    slug = models.SlugField('Slug название', unique=True, max_length=500)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'


class Polls(models.Model):
    """Модель опросов"""

    title = models.CharField('Заголовок', max_length=500)
    description = models.CharField('Описание', max_length=500)
    category = models.CharField('Категория', max_length=500)
    points = models.IntegerField('Баллы', default=10)
    latePosting = models.BooleanField('Отложная публикация?', default=False)
    datePosting = models.DateTimeField('Дата и время публикации', default=datetime.now())
    in_archive = models.BooleanField('Архивный опрос?', default=False)
    session = models.ForeignKey('SessionTC', on_delete=models.CASCADE, to_field='number_session', null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Опрос'
        verbose_name_plural = 'Опросы'


class Questions(models.Model):
    """Модель вопросов и ответов"""

    poll = models.ForeignKey(Polls, on_delete=models.CASCADE)
    question = models.CharField('Вопрос', max_length=500, unique=False)
    answer = models.CharField('Ответ', max_length=500)
    freeAnswer = models.BooleanField('Свободный ответ', default=False, null=True)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Rating(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, to_field='username', related_name='Пользователь',
                                    default=None)
    points = models.IntegerField('Баллы', default=0)
    rating = models.IntegerField('Рейтинг', default=100000)

    def __str__(self):
        return self.username.username

    class Meta:
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинг'


class RatingTeam(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, to_field='name', default=None, related_name='Команда')
    session = models.ForeignKey("SessionTC", on_delete=models.CASCADE, to_field='number_session', default=None,
                                related_name='Сессия')
    points = models.IntegerField('Баллы', default=0)
    rating = models.IntegerField('Рейтинг', default=100000)

    def __str__(self):
        return self.team.name

    class Meta:
        verbose_name = 'Рейтинг команды'
        verbose_name_plural = 'Рейтинг команды'


class SessionTC(models.Model):
    number_session = models.IntegerField('Номер смены', default=0, unique=True)
    name_session = models.CharField('Название смены', default='Смена не определена', unique=True, max_length=500)
    date_from_session = models.DateField('Дата начала смены', null=True, blank=True)
    date_to_session = models.DateField('Дата конца смены', null=True, blank=True)
    active_session = models.BooleanField('Активная смена', default=False, null=True)

    def __str__(self):
        return self.name_session

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'
        ordering = ['number_session']


class PollsCheck(models.Model):
    user_valuer = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name='Оценщик', related_name="ids",
                                    null=True)
    poll_user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name='Кого оценили', blank=True, null=True)
    poll = models.ForeignKey(Polls, on_delete=models.CASCADE, verbose_name='Опрос')

    class Meta:
        verbose_name = 'Пройденный опрос'
        verbose_name_plural = 'Пройденные опросы'


class QuestionsCheck(models.Model):
    question = models.ForeignKey(Questions, on_delete=models.CASCADE, verbose_name='Вопрос')
    answer = models.CharField('Ответ', max_length=500)
    user_valuer = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name='Оценщик')
    poll = models.ForeignKey(Polls, on_delete=models.CASCADE, verbose_name='Опрос')
    poll_check = models.ForeignKey(PollsCheck, on_delete=models.CASCADE, default=None,
                                   verbose_name='ID пройденного опроса')

    def __str__(self):
        return self.question.question

    class Meta:
        verbose_name = 'Ответ на вопрос'
        verbose_name_plural = 'Ответы на вопросы'


class LogPoint(models.Model):
    username = models.CharField('Пользователь', max_length=500)
    points = models.IntegerField('Баллы', default=0)
    date = models.DateTimeField('Дата зачисления')
    poll = models.CharField('Опрос', max_length=500)
    add = models.BooleanField('Зачисление', null=True)

    def __str__(self):
        return '%s %s %s' % (self.username, self.points, self.date)

    class Meta:
        verbose_name = 'Логи зачисления баллов'
        verbose_name_plural = 'Логи зачисления баллов'
        ordering = ['-date']


class FileUpload(models.Model):
    file = models.FileField(upload_to='fileUpload/')


class Test(models.Model):
    title = models.CharField('Заголовок теста', null=False, max_length=500)
    description = models.TextField('Описание теста')
    points = models.IntegerField('Баллы за прохождение')
    session = models.ForeignKey(SessionTC, on_delete=models.CASCADE, related_name='Смена', to_field='number_session')
    num_comp = models.ForeignKey('NumComp', on_delete=models.CASCADE, related_name='Компетенция', to_field='number')
    latePosting = models.BooleanField('Отложная публикация?', default=False)
    in_archive = models.BooleanField('Архивный опрос?', default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'


class NumComp(models.Model):
    number = models.IntegerField('Номер компетенции', unique=True)

    def __str__(self):
        return str(self.number)


class QuestionsTest(models.Model):
    question = models.CharField('Вопрос', null=False, max_length=500)
    test = models.ForeignKey(Test, related_name='Тест', on_delete=models.CASCADE)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Вопрос на тест'
        verbose_name_plural = 'Вопросы на тест'


class AnswersTest(models.Model):
    answer = models.CharField('Ответ', null=False, max_length=500)
    points = models.IntegerField('Баллы', default=0, null=False)
    question = models.ForeignKey(QuestionsTest, related_name='Вопрос', on_delete=models.CASCADE)

    def __int__(self):
        return self.question

    class Meta:
        verbose_name = 'Ответ на тест'
        verbose_name_plural = 'Ответы на тест'


class CheckTest(models.Model):
    test = models.ForeignKey(Test, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False, related_name='Пользователь')

    def __int__(self):
        return self.test

    class Meta:
        verbose_name = 'Пройденный тест'
        verbose_name_plural = 'Пройденные тесты'


class QuestionsCheckTest(models.Model):
    question = models.ForeignKey(QuestionsTest, on_delete=models.CASCADE, verbose_name='Вопрос')
    answer = models.CharField('Ответ', max_length=500)
    user_valuer = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name='Оценщик')
    poll = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Test')
    poll_check = models.ForeignKey(CheckTest, on_delete=models.CASCADE, default=None,
                                   verbose_name='ID пройденного теста')
    point = models.IntegerField('Points', default=0)

    def __str__(self):
        return self.question.question

    class Meta:
        verbose_name = 'Ответ на вопрос Теста'
        verbose_name_plural = 'Ответы на вопросы Теста'


class SmtpServer(models.Model):
    host = models.CharField("Имя хоста (example.ru)", max_length=255)
    port = models.IntegerField("Порт")
    email = models.CharField("Электронная почта отправителя", max_length=255)
    password = models.CharField("Пароль от электронной почты", max_length=255)
    created_date = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'SMTP сервер'
        verbose_name_plural = 'SMTP сервер'