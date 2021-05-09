from decimal import Decimal

from django import template

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date, datetime

from online_users.models import OnlineUserActivity

from ..models import Genre, Rating, RatingStar, Chapter

register = template.Library()


# Фильтр для проверки юзера в объекте(Типа, если лайк уже ставил или диз)
# except на ТайпЕррор, надо бы добавить, а то НоН обжект хэв но филтер ёба
@register.filter
def user_in(objects, user):
    if user.is_authenticated:
        try:
            return objects.filter(user=user).exists()
        except:
            return False
    return False


@register.simple_tag
def age(born_date):
    if date.today().month > born_date.month:
        return (date.today().year - born_date.year)
    elif born_date.month == date.today().month and date.today().day > born_date.day:
        return date.today().year - born_date.year
    else:
        return date.today().year - born_date.year - 1


@register.inclusion_tag('core/include/genres.html')
def genres():
    return {'all_genres': Genre.objects.all()}


@register.filter
def star_user(novell, user):
    try:
        a = Rating.objects.get(author=user, novell=novell)
        return a.rate.value
    except:
        return False


@register.inclusion_tag('core/include/stars.html')
def stars(rating):
    try:
        a = round(rating)
    except:
        return {'stars': RatingStar.objects.filter(value__gt=0).order_by('value'), 'rating': 0, 'half': False,
                'rating_plus': 0, 'rounded': 0}
    a = round(rating)
    if abs(a - rating) > Decimal('0.25') and abs(a - rating) < Decimal('0.75'):
        half = True
    else:
        half = False
    rating_plus = rating + 1
    return {'stars': RatingStar.objects.filter(value__gt=0).order_by('value'), 'rating': rating, 'half': half,
            'rating_plus': rating_plus, 'rounded': a}


@register.filter
def user_already_rate(user, novell):
    nov = novell.reviews_to_novell.filter(author=user)
    if nov:
        return True
    else:
        return False


@register.filter
def user_already_read(user, novell):
    nov = novell.rating_set.filter(author=user)
    if nov:
        return True
    else:
        return False


@register.filter
def first_chapter(novell):
    return novell.chapters.filter(status=True).first()


@register.filter
def first_chapter_link(novell):
    a = novell.chapters.filter(status=True).first()
    if a:
        return a.id
    else:
        return 0


@register.filter
def novell_unread(user, novell):
    a = set(user.user_profile.chapter_readed.all())
    b = set(novell.chapters.all())
    if len(a & b) == 0:
        return True
    else:
        return False


@register.filter
def novell_readed(user, novell):
    a = set(user.user_profile.chapter_readed.all())
    b = set(novell.chapters.filter(status=True))
    if b <= a:
        return True
    else:
        return False


@register.filter
def last_unread_chapter(user, novell):
    a = set(user.user_profile.chapter_readed.all())
    b = set(novell.chapters.filter(status=True))
    x = list(b - a)
    x.sort(key=lambda l: l.number)
    if len(x) > 0:
        return x[0].number


@register.inclusion_tag('core/include/profile/last_activity.html')
def user_last_activity(user):
    try:
        a = OnlineUserActivity.objects.get(user=user)
        is_online = timezone.now() - a.last_activity < timezone.timedelta(minutes=5)
    except:
        return None
    return {'last_seen': a.last_activity,
            'is_online': is_online}
