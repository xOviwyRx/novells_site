from django.db import models

# Create your models here.
from django.utils import timezone


class Novell(models.Model):
    original_title = models.CharField(max_length=256, verbose_name='Оригинальное название')
    rus_title = models.CharField(max_length=256, verbose_name='Перевод названия', blank=True, null=True)
    slug = models.SlugField(max_length=250)
    author = models.CharField(max_length=128, verbose_name='Автор')
    translator = models.CharField(max_length=128, verbose_name='Переводчик')
    publish = models.DateTimeField('Начало публикации', default=timezone.now)
    created = models.DateTimeField('Опубликовано', auto_now_add=True)
    poster = models.ImageField('Постер', upload_to='users_avatars/', default='users_avatars/default/default.png')
    description = models.TextField('Описание')


class Chapter(models.Model):
    number = models.PositiveSmallIntegerField('Номер главы')
    title = models.CharField('Заголовок главы', max_length=256)
    publish = models.DateTimeField('Дата публикации', default=timezone.now)
    novell = models.ForeignKey(Novell, verbose_name='Новелла', on_delete=models.PROTECT, related_name='chapters')
