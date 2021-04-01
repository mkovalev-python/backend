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

    country = models.CharField('Город', max_length=255, unique=True)

    def __str__(self):
        return self.country

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class Team(models.Model):
    """Модель команд"""

    name = models.CharField('Название команды', unique=True, max_length=255)

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

    name = models.CharField('Роли', unique=True, max_length=100)
    slug = models.SlugField('Slug название', unique=True, max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'


class Polls(models.Model):
    """Модель опросов"""

    title = models.CharField('Заголовок', max_length=255)
    description = models.CharField('Описание', max_length=510)
    category = models.CharField('Категория', max_length=100)
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
    question = models.CharField('Вопрос', max_length=255)
    answer = models.CharField('Ответ', max_length=255)

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


class SessionTC(models.Model):
    number_session = models.IntegerField('Номер смены', default=0, unique=True)
    name_session = models.CharField('Название смены', default='Смена не определена', unique=True, max_length=50)
    date_from_session = models.DateField('Дата начала смены', null=True, blank=True)
    date_to_session = models.DateField('Дата конца смены', null=True, blank=True)
    active_session = models.BooleanField('Активная смена', default=False, null=True)

    def __str__(self):
        return self.name_session

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'
        ordering = ['number_session']
