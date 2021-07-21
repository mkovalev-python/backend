# Generated by Django 3.1.7 on 2021-07-16 08:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='questions',
            name='freeAnswer',
            field=models.BooleanField(default=False, verbose_name='Свободный ответ'),
        ),
        migrations.AlterField(
            model_name='polls',
            name='datePosting',
            field=models.DateTimeField(default=datetime.datetime(2021, 7, 16, 11, 11, 6, 120507), verbose_name='Дата и время публикации'),
        ),
    ]