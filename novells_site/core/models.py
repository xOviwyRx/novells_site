from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Create your models here.
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone


class MyQuerySet(models.query.QuerySet):

    def delete(self):
        for obj in self:
            obj.delete()


# Менеджер модели лайк-дизлайк
class LikeDislikeManager(models.Manager):
    use_for_related_fields = True

    def likes(self):
        # Забираем queryset с записями больше 0
        return self.get_queryset().filter(vote__gt=0)

    def dislikes(self):
        # Забираем queryset с записями меньше 0
        return self.get_queryset().filter(vote__lt=0)

    def sum_rating(self):
        # Забираем суммарный рейтинг
        return self.get_queryset().aggregate(Sum('vote')).get('vote__sum') or 0

    def posts(self):
        return self.get_queryset().filter(content_type__model='post').order_by('-posts__pub_date')

    def comments(self):
        return self.get_queryset().filter(content_type__model='comment').order_by('-comments__pub_date')

    def get_queryset(self):
        return MyQuerySet(self.model, using=self._db)


# Модель для лайк-дизлайк системы
class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1

    VOTES = (
        (DISLIKE, 'Не нравится'),
        (LIKE, 'Нравится')
    )

    vote = models.SmallIntegerField(verbose_name="Голос", choices=VOTES)
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = LikeDislikeManager()

    def get_query_set(self):
        return MyQuerySet(self.model)

    class Meta:
        verbose_name = 'Лайк/дизлайк голос'
        verbose_name_plural = "Лайк/дизлайк голоса"


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
    rus_title = models.CharField(max_length=256, verbose_name='Название на русском', blank=True, null=True)
    eng_title = models.CharField(max_length=256, verbose_name='Название на англ.', blank=True, null=True)

    slug = models.SlugField(max_length=250)
    author = models.CharField(max_length=128, verbose_name='Автор')
    translator = models.CharField(max_length=128, verbose_name='Переводчик', default='Privereda1')
    publish = models.DateTimeField('Начало публикации', default=timezone.now)
    status = models.CharField('Статус', max_length=2, choices=STATUS, default=ANONS)
    important = models.BooleanField('Выбор редакции', default=False)
    created = models.DateTimeField('Опубликовано', auto_now_add=True)
    poster = models.ImageField('Постер', upload_to='novells_poster/')
    description = models.TextField('Описание')
    genres = models.ManyToManyField(Genre, related_name='novells', verbose_name='Жанры')
    views = models.PositiveSmallIntegerField('Просмотры', default=0)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, verbose_name='Рейтинг', default='0.00')

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

    def get_comments(self):
        return self.chapter_comments.filter(parent__isnull=True)


class Comment(models.Model):
    chapter = models.ForeignKey(Chapter, verbose_name='К главе', on_delete=models.CASCADE,
                                related_name='chapter_comments')
    author = models.ForeignKey(User, verbose_name='Автор', related_name='comments_by_user', on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', verbose_name='Родитель', on_delete=models.SET_NULL, blank=True, null=True,
                               related_name="childs")
    votes = GenericRelation(LikeDislike, related_query_name='comments')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)

    def __str__(self):
        return 'Комментарий от {} к {}'.format(self.author, self.chapter.title)

    def get_absolute_url(self):
        a = reverse('core:chapter_detail', args=[self.chapter.novell.slug, self.chapter.number]) + '#comment' + str(
            self.id)
        return a


class Profile(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    UNKNOWN = 'UN'
    GENDER = [
        (MALE, 'Мужской'),
        (FEMALE, 'Женский'),
        (UNKNOWN, 'Неизвестно')
    ]
    name = models.OneToOneField(User, verbose_name='Пользователь', on_delete=models.CASCADE,
                                related_name='user_profile')

    realname = models.CharField('Имя',max_length=100, blank=True)
    sex = models.CharField('Пол', max_length=2, choices=GENDER, default=UNKNOWN)
    slug = AutoSlugField(always_update=True, populate_from='name')
    avatar = models.ImageField('Аватар', upload_to='users_avatars/', default='users_avatars/default/default.png')
    born_date = models.DateField('Дата рождения', blank=True, null=True)
    about = models.TextField(max_length=1000, blank=True)
    city = models.CharField(max_length=100, blank=True)
    vk = models.CharField(max_length=100, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    discord = models.CharField(max_length=100, blank=True)
    bookmarks = models.ManyToManyField(Novell, blank=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(name=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.user_profile.save()

    def get_absolute_url(self):
        return reverse('core:profile_detail', args=[self.id, self.slug])

    def __str__(self):
        return 'Профиль {}'.format(self.name.username)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'


class RatingStar(models.Model):

    value = models.SmallIntegerField('Значение', default=0)

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Значения оценок"
        ordering = ['-value']


class Rating(models.Model):

    author = models.ForeignKey(User, verbose_name='Проголосовавший', related_name='rated_novells', on_delete=models.CASCADE)
    rate = models.ForeignKey(RatingStar, verbose_name='Оценка', on_delete=models.CASCADE)
    novell = models.ForeignKey(Novell, verbose_name='Новелла', on_delete=models.CASCADE)
    date = models.DateTimeField("Дата оценки", auto_now_add=True)
    updated = models.DateTimeField("Дата обновления оценки", auto_now=True)

    def __str__(self):
        return '{} от {} новелле {}'.format(self.rate, self.author, self.novell)

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'


class Slider(models.Model):
    shot = models.ImageField('Картинка', upload_to='slider_shots/', default='slider_shots/default.png')
    position = models.PositiveSmallIntegerField('Позиция')
    text_primary = models.CharField("Крупный текст", max_length=100, blank=True)
    text_secondary = models.CharField("Текст помельче", max_length=100, blank=True)
    active = models.BooleanField('Показывать', default=True)

    def __str__(self):
        return 'Картинка на главной на {} месте'.format(self.position)

    class Meta:
        verbose_name = 'Картинка на главной'
        verbose_name_plural = 'Картинки на главной'

