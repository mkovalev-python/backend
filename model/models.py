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
    avatar = models.ImageField('Аватар', width_field=400, height_field=400)

    def __str__(self):
        return self.username

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
