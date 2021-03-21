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
    avatar = models.ImageField('Аватар', upload_to='avatar/',)

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
