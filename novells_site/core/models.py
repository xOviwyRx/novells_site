from django.db import models

# Create your models here.
from django.urls import reverse
from django.utils import timezone


class Genre(models.Model):
    title = models.CharField('Жанр', max_length=256)
    description = models.TextField('Описание', blank=True, null=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('-title',)

    def __str__(self):
        return self.title


class Novell(models.Model):
    ANONS = 'AN'
    ONGOING = 'OG'
    COMPLETED = 'CT'
    STATUS = [
        (ANONS, 'Анонс'),
        (ONGOING, 'Выходит'),
        (COMPLETED, 'Завершено')
    ]

    original_title = models.CharField(max_length=256, verbose_name='Оригинальное название')
    rus_title = models.CharField(max_length=256, verbose_name='Перевод названия', blank=True, null=True)
    slug = models.SlugField(max_length=250)
    author = models.CharField(max_length=128, verbose_name='Автор')
    translator = models.CharField(max_length=128, verbose_name='Переводчик')
    publish = models.DateTimeField('Начало публикации', default=timezone.now)
    status = models.CharField('Статус', max_length=2, choices=STATUS, default=ANONS)
    created = models.DateTimeField('Опубликовано', auto_now_add=True)
    poster = models.ImageField('Постер', upload_to='novells_poster/')
    description = models.TextField('Описание')
    genres = models.ManyToManyField(Genre, related_name='novells', verbose_name='Жанры')
    views = models.PositiveSmallIntegerField('Просмотры', default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, verbose_name='Рейтинг')

    def get_absolute_url(self):
        return reverse('core:novell_detail', args=[self.slug])

    class Meta:
        verbose_name = 'Новелла'
        verbose_name_plural = 'Новеллы'

    def __str__(self):
        return self.original_title


class Chapter(models.Model):
    number = models.PositiveSmallIntegerField('Номер главы')
    title = models.CharField('Заголовок главы', max_length=256)
    status = models.BooleanField('Выпущена', help_text='Если вышла, галочка стоит. Нет - запланирована', default=False)
    publish = models.DateTimeField('Дата публикации', default=timezone.now)
    novell = models.ForeignKey(Novell, verbose_name='Новелла', on_delete=models.PROTECT, related_name='chapters')
    chapter_text = models.TextField('Текст главы', blank=True, null=True)

    def get_absolute_url(self):
        return reverse('core:chapter_detail', args=[self.novell.slug, self.number])


    class Meta:
        verbose_name = 'Глава'
        verbose_name_plural = 'Главы'
        ordering = ('number', '-publish',)

    def __str__(self):
        return 'Глава {} Новеллы {} '.format(self.number, self.novell)
