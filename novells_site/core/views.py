import json
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required

from .models import Novell, Chapter, LikeDislike, Profile, Genre, Rating, Slider, Post, Review, RatingStar, Comment, UserBalanceChange, ViewNovell
from .forms import CommentForm, EditProfileForm, RatingForm
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from rest_framework import viewsets, filters, views
from rest_framework.response import Response
from .serializers import NovellListSerializer
import yookassa
import var_dump as var_dump
from yookassa.domain.models.currency import Currency
from yookassa.domain.models.receipt import Receipt
from yookassa.domain.models.receipt_item import ReceiptItem
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.request.payment_request_builder import PaymentRequestBuilder
import json
from django.http import HttpResponse
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotification
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from datetime import date

# Create your views here.


#Configuration.account_id = '819176'
#Configuration.secret_key = 'live__QoWec5bBgd00kgqy4xnSz245AQk2faiTHjPJN7tkiQ' # Old key
#Configuration.secret_key = 'live_UaQb6za_zudoklGWzklf1GMIief0Yrhr7Q-YGtV-LsU'

# Configuration.account_id = '829811'
# Configuration.secret_key = 'test__QoWec5bBgd00kgqy4xnSz245AQk2faiTHjPJN7tkiQ'
# test_3z2IRsWt9h2FRrKVBy9AaGkeMHt6appEWllT9614G5k


@login_required
def pay_prepare(request):
    return render(request, 'core/include/pay_prepare.html')


@login_required
def donate_money(request):
    Configuration.account_id = '819176'
    Configuration.secret_key = 'live_Rj4b50yCpOzEirnhaHWgSJ_f-t9naP6WBSlAk8WlAss'

    #Configuration.account_id = '829811'
    #Configuration.secret_key = 'test_3z2IRsWt9h2FRrKVBy9AaGkeMHt6appEWllT9614G5k'


    # Configuration.configure('819176', 'test__QoWec5bBgd00kgqy4xnSz245AQk2faiTHjPJN7tkiQ')
    receipt = Receipt()
    receipt.customer = {"phone": "79990000000", "email": "test@email.com"}
    receipt.tax_system_code = 1
    receipt.items = [
        ReceiptItem({
            "description": "Пополнения баланса на сумму {}".format(request.POST.get('sum')),
            "quantity": 1,
            "amount": {
                "value": request.POST.get('sum'),
                "currency": Currency.RUB
            },
            "vat_code": 2,
            "capture":True
        }),
    ]

    s = {'user': str(request.user)}
    print(request.user)

    builder = PaymentRequestBuilder()
    builder.set_amount({"value": request.POST.get('sum'), "currency": Currency.RUB}) \
        .set_confirmation({"type": ConfirmationType.REDIRECT, "return_url": "https://privereda1.ru"}) \
        .set_capture(True) \
        .set_description("Заказ №72") \
        .set_metadata({"user": int(request.user.id)}) \
        .set_receipt(receipt)

    request = builder.build()
    # Можно что-то поменять, если нужно
    res = Payment.create(request)
    print(res.json())
    a = json.loads(res.json())
    print(a['confirmation']['confirmation_url'])
    var_dump.var_dump(res)
    # print(request.POST)
    # print(request.POST.get('sum'))
    return redirect(a['confirmation']['confirmation_url'])
    # return HttpResponse('Временно недоступен')


@csrf_exempt
def my_webhook_handler(request):
    Configuration.account_id = '819176'
    Configuration.secret_key = 'live_Rj4b50yCpOzEirnhaHWgSJ_f-t9naP6WBSlAk8WlAss'

    #Configuration.account_id = '829811'
    #Configuration.secret_key = 'test_3z2IRsWt9h2FRrKVBy9AaGkeMHt6appEWllT9614G5k'


    # Извлечение JSON объекта из тела запроса
    print(request)

    event_json = json.loads(request.body)
    print(event_json)
    try:
        # Создание объекта класса уведомлений в зависимости от события
        notification_object = WebhookNotification(event_json)
        response_object = notification_object.object
        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payed_user = response_object.metadata['user']
            payed_money = response_object.amount.value
            # UserBalanceChange.objects.create(user=payed_user, amount=payed_money)
            print(payed_user, payed_money)
            p = Profile.objects.get(name_id=payed_user)
            p.balance += payed_money
            p.save(update_fields=['balance'])
            some_data = {
                'paymentId': response_object.id,
                'paymentStatus': response_object.status,
            }
            print(some_data)
    except Exception:
        # Обработка ошибок
        return HttpResponse(status=400)  # Сообщаем кассе об ошибке

    return HttpResponse(status=200)  # Сообщаем кассе, что все хорошо


def js_filter_test(request):
    return render(request, 'core/novells_list_new.html')


class GenreYear:

    def get_genres(self):
        return Genre.objects.all()

    def get_year(self):
        return Novell.objects.all().order_by('publish__year').values_list('publish__year').distinct()

    def get_status(self):
        return Novell.objects.all().values_list('status').distinct()


def contact(request):
    return render(request, 'core/contacts.html')


def index(request):

    h = request.get_host()
    if h == 'www.privereda1.ru' or h == 'privereda1.ru':
        pop_novell = Novell.objects.filter(important=True, translator='Privereda1')
        # pop_novell = Novell.objects.order_by('-views').first()
        test = pop_novell.first()
        shedule_chapter = Chapter.objects.filter(novell__translator='Privereda1').order_by('-created')[:8]
        all_novells = Novell.objects.filter(translator='Privereda1').order_by('-views')[:6]
        shots = Slider.objects.filter(active=True, translator='Privereda1').order_by('position')

        return render(request, 'core/home.html', {'pops': pop_novell,
                                                  'last_update': shedule_chapter,
                                                  'all_novells': all_novells,
                                                  'image_shots': shots,
                                                  'test': test
                                                  })
    else:
        pop_novell = Novell.objects.filter(important=True, translator='Oksiji13')
        # pop_novell = Novell.objects.order_by('-views').first()
        test = pop_novell.first()
        shedule_chapter = Chapter.objects.filter(novell__translator='Oksiji13').order_by('-created')[:8]
        all_novells = Novell.objects.filter(translator='Oksiji13').order_by('-views')[:6]
        shots = Slider.objects.filter(active=True, translator='Oksiji13').order_by('position')

        return render(request, 'core/home_second.html', {'pops': pop_novell,
                                                         'last_update': shedule_chapter,
                                                         'all_novells': all_novells,
                                                         'image_shots': shots,
                                                         'test': test
                                                         })

class NovellDetailView(GenreYear, DetailView):
    model = Novell
    context_object_name = 'novell'
    template_name = 'core/novell_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nov = context['novell']
        nov.views = nov.views + 1
        nov.save()
        if self.request.user.is_staff == False:
            ViewNovell.objects.create(novell = nov)
        context['star_form'] = RatingForm()

        return context

    def post(self, request, slug):
        data = request.POST
        novell = get_object_or_404(Novell, slug=slug)
        if request.user.is_anonymous or data['body'] is None:
            return redirect(novell.get_absolute_url())
        try:
            a = Review.objects.get(author=request.user, novell=novell)
            return redirect(novell.get_absolute_url())
        except:
            Review.objects.create(author=request.user, body=data['body'], title=data['title'], novell=novell)
        return redirect(novell.get_absolute_url())


class ChapterDetailView(DetailView):
    model = Chapter
    context_object_name = 'chapter'
    template_name = 'core/chapter_detail.html'

    def get_object(self):
        novell = get_object_or_404(Novell, slug=self.kwargs['slug'])
        chapter = get_object_or_404(Chapter, novell=novell, number=self.kwargs['number'])
        #

        if not self.request.user.is_anonymous:
            self.request.user.user_profile.chapter_readed.add(chapter)
        else:
            raise PermissionDenied
            #return redirect('accounts/signup/')
            #return redirect(novell.get_absolute_url())
            #return redirect('account_signup')


        if not chapter.premium:
            return chapter

        elif not self.request.user.is_anonymous and chapter not in self.request.user.user_profile.buyed_chapters.all():
            # "Вы пытаетесь открыть платную главу. Купите её, это не так дорого!"
            raise PermissionDenied
            #return redirect('accounts/signup/')
            #return redirect(novell.get_absolute_url())

        elif not self.request.user.is_anonymous and chapter in self.request.user.user_profile.buyed_chapters.all():
            return chapter
        else:
            raise PermissionDenied
            #return redirect('accounts/signup/')
            #return redirect(novell.get_absolute_url())


    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if not self.object:
                raise PermissionDenied
        except PermissionDenied:
            return redirect('https://'+request.get_host()+'/accounts/signup/', permanent=True)
        context = self.get_context_data(object=self.object)

        if request.user.is_staff == False:
            ViewNovell.objects.create(novell = context['chapter'].novell)

        return self.render_to_response(context)


#            raise Http404('Неизвестная ошибка')


"""
    def get_object(self):
        nov = get_object_or_404(Novell, slug=self.kwargs['slug'])
        if not self.request.user.is_anonymous:
            self.request.user.user_profile.chapter_readed.add(
                get_object_or_404(Chapter, novell=nov, number=self.kwargs['number']))
        return get_object_or_404(Chapter, novell=nov, number=self.kwargs['number'])
"""

"""
        #
        if chapter.premium and self.request.user.is_anonymous:
            return HttpResponse("Вы пытаетесь открыть платную главу. Войдите в аккаунт, где она куплена, или купите её!")
        elif self.request.user.is_anonymous and chapter.premium and chapter not in self.request.user.user_profile.buyed_chapters.all():
            :raise HttpResponse(
                "Вы пытаетесь открыть платную главу. Купите её, это не так дорого!")
        elif self.request.user.is_anonymous and chapter.premium and chapter in self.request.user.user_profile.buyed_chapters.all():
            return chapter
        else:
            return HttpResponse('Неизвестная ошибка')
"""


class AddComment(View):
    model = None

    def post(self, request, pk):
        obj = self.model.objects.get(id=pk)
        if request.method == 'POST':
            form = CommentForm(data=request.POST)
            if form.is_valid():
                form = form.save(commit=False)
                if request.POST.get("parent", None):
                    form.parent_id = int(request.POST.get("parent"))
                form.object_id = obj.id
                form.chapter = obj
                form.author = request.user
                form.content_type = ContentType.objects.get_for_model(obj)
                form.save()
            return redirect(form.get_absolute_url())


class VotesView(View):
    model = None  # Модель данных - Статьи или Комментарии
    vote_type = None  # Тип комментария Like/Dislike

    def post(self, request, id):
        obj = self.model.objects.get(id=id)
        # author_profile = obj.author.user_profile
        # GenericForeignKey не поддерживает метод get_or_create
        try:
            likedislike = LikeDislike.objects.get(content_type=ContentType.objects.get_for_model(obj), object_id=obj.id,
                                                  user=request.user)

            if likedislike.vote is not self.vote_type:
                likedislike.vote = self.vote_type
                likedislike.save(update_fields=['vote'])
                result = True
            else:
                # if obj.author != request.user:
                #    author_profile.karma -= likedislike.vote
                #    author_profile.save(update_fields=['karma'])
                likedislike.delete()
                result = False

        except LikeDislike.DoesNotExist:
            obj.votes.create(user=request.user, vote=self.vote_type)
            result = True

        return HttpResponse(
            json.dumps({
                "result": result,
                "like_count": obj.votes.likes().count(),
                "dislike_count": obj.votes.dislikes().count(),
                "sum_rating": obj.votes.sum_rating()
            }),
            content_type="application/json"
        )


class GetNotificationView(View):

    def post(self, request):
        prof = request.user.user_profile
        my_news = Chapter.objects.filter(Q(novell__in=prof.bookmarks.all()) | Q(novell__in=prof.planned.all()),
                                         created__gte=prof.news_check)
        list_news = Chapter.objects.filter(
            Q(novell__in=prof.bookmarks.all()) | Q(novell__in=prof.planned.all()) | Q(
                novell__in=prof.in_process_reading.all()) | Q(novell__in=prof.readed.all())).order_by('-created')[:10]

        new_coms = Comment.objects.filter(~Q(author=request.user), parent__author=request.user,
                                          created__gte=prof.news_check)
        news_count = my_news.count() + new_coms.count()
        comments_reply = Comment.objects.filter(~Q(author=request.user), parent__author=request.user).order_by(
            '-created')[:10]

        # min_cr = max(list_news[0].created, comments_reply[0].created)
        # print(comments_reply, min_cr)
        if news_count < 5:
            a = list(list_news) + list(comments_reply)
            b = sorted(a, key=lambda x: x.created, reverse=True)[:5]
        else:
            a = list(my_news) + list(new_coms)
            b = sorted(a, key=lambda x: x.created, reverse=True)

        result = news_count > 0

        if result:
            return HttpResponse(
                json.dumps({
                    "result": result,
                    "news_count": news_count,
                    "notifications_list": render_to_string('core/include/notifications_list.html',
                                                           {'user': request.user, 'my_news': b}),
                }),
                content_type="application/json"
            )
        else:
            return HttpResponse(
                json.dumps({
                    "result": result,
                    "notifications_list": render_to_string('core/include/notifications_list.html',
                                                           {'user': request.user, 'my_news': b}),
                }),
                content_type="application/json"
            )


class GetNotificationNewsView(View):

    def post(self, request):
        prof = request.user.user_profile
        my_news = Post.objects.filter(created__gte=prof.new_post_check)
        result = my_news.count() > 0
        print(my_news, my_news.count())
        if result:
            return HttpResponse(
                json.dumps({
                    "result": result,
                    "news_count": my_news.count(),
                }),
                content_type="application/json"
            )
        else:
            return HttpResponse(
                json.dumps({
                    "result": result,
                }),
                content_type="application/json"
            )


class CheckNotificationView(View):
    def post(self, request):
        request.user.user_profile.news_check = timezone.now()
        request.user.user_profile.save()
        return HttpResponse(200)


@login_required
def add_to_bookmark(request, pk, type_of):
    nov = get_object_or_404(Novell, pk=pk)
    if type_of == 'bookmark':
        request.user.user_profile.bookmarks.add(nov)
    if type_of == 'planned':
        request.user.user_profile.planned.add(nov)
    if type_of == 'reading':
        request.user.user_profile.in_process_reading.add(nov)
    elif type_of == 'readed':
        request.user.user_profile.readed.add(nov)
        try:
            a = Rating.objects.get(author=request.user,
                                   novell_id=pk)
            if a:
                return redirect(nov.get_absolute_url())
        except:
            rate_readed = RatingStar.objects.get(value=0)
            Rating.objects.update_or_create(
                author=request.user,
                novell_id=pk,
                rate=rate_readed
            )
    return redirect(nov.get_absolute_url())


@login_required
def del_from_bookmark(request, pk, type_of, frommm):
    nov = get_object_or_404(Novell, pk=pk)
    if type_of == 'bookmark':
        request.user.user_profile.bookmarks.remove(nov)
    elif type_of == 'planned':
        request.user.user_profile.planned.remove(nov)
    if type_of == 'reading':
        request.user.user_profile.in_process_reading.remove(nov)
    elif type_of == 'readed':
        request.user.user_profile.readed.remove(nov)

        try:
            a = Rating.objects.get(author=request.user,
                                   novell_id=pk)
            print(a)
            a.delete()
        except:
            return HttpResponse('Криво сработало удаление из прочитанных')

    if frommm == 'profile':
        return redirect(request.user.user_profile.get_absolute_url())
    else:
        return redirect(nov.get_absolute_url())


@login_required
def buy_chapter(request, pk):
    chapter = get_object_or_404(Chapter, id=pk)
    if chapter.premium and chapter.cost <= request.user.user_profile.balance:
        request.user.user_profile.balance -= chapter.cost
        request.user.user_profile.save(update_fields=["balance"])
        request.user.user_profile.buyed_chapters.add(chapter)
        create_transaction(request.user, chapter.cost, chapter.novell)
        return redirect(chapter.get_absolute_url())
    else:
        return HttpResponse('Недостаточно средств или просто кривой разраб, сорри((')


@login_required
def buy_many_chapters(request, pk):
    n = get_object_or_404(Novell, id=pk)
    sum_cost = 0
    for i in request.POST.getlist('chosen'):
        chapter = get_object_or_404(Chapter, id=int(i))
        sum_cost += chapter.cost
    if sum_cost <= request.user.user_profile.balance:
        request.user.user_profile.balance -= sum_cost
        request.user.user_profile.save(update_fields=["balance"])
        create_transaction(request.user, sum_cost, n)
        for i in request.POST.getlist('chosen'):
            chapter = get_object_or_404(Chapter, id=i)
            request.user.user_profile.buyed_chapters.add(chapter)
        return redirect(n.get_absolute_url())
    else:
        return HttpResponse('Недостаточно средств или сбой системы')

def create_transaction(user, amount, novell):
    if user.is_staff == False:
        UserBalanceChange.objects.create(user=user, amount=amount, novell=novell)

class ProfileDetail(DetailView):
    model = Profile
    context_object_name = 'profile'
    template_name = 'core/profile/profile_detail.html'


class EditMyProfile(DetailView, View):
    model = Profile
    context_object_name = 'profile'
    template_name = 'core/profile/edit_profile.html'

    def post(self, request, pk, slug):
        profile = Profile.objects.get(id=pk)
        if request.user == profile.name:
            profile_form = EditProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                if 'avatar' in request.FILES:
                    profile.avatar = request.FILES['avatar']
                profile_form.save()
            return redirect(profile.get_absolute_url())
        else:
            return HttpResponse('Permission deny')


class NovellListView(GenreYear, ListView):
    template_name = 'core/novells_list.html'
    model = Novell
    context_object_name = 'novells'


class FilterNovellsView(GenreYear, ListView):
    template_name = 'core/novells_list.html'
    context_object_name = 'novells'

    def get_queryset(self):
        q = self.request.GET.get('q')
        if self.request.get_host() == 'www.privereda1.ru' or self.request.get_host() == 'privereda1.ru':
            translator = 'Privereda1'
        else:
            translator = 'Oksiji13'
        if q:
            return Novell.objects.filter(rus_title__icontains=q, translator=translator)
        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        if genre_filter and year_filter and len(genre_filter) == 1:
            return Novell.objects.filter(publish__year__in=year_filter, genres__in=genre_filter, translator=translator)
        elif len(genre_filter) > 1 and year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.filter(publish__year__in=year_filter, translator=translator):
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            return a
        elif len(genre_filter) > 1 and not year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.filter(translator=translator):
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            return a
        elif not year_filter and not genre_filter:
            return Novell.objects.filter(translator=translator)
        else:
            return Novell.objects.filter((Q(publish__year__in=year_filter) | Q(genres__in=genre_filter)) and Q(translator=translator)).distinct()
        # print(self.request.GET.getlist('year'))


class AddNovellRating(View):

    def post(self, request):
        form = RatingForm(request.POST)
        if form.is_valid():
            nov = Novell.objects.get(id=int(request.POST.get("novell")))

            Rating.objects.update_or_create(
                author=self.request.user,
                novell_id=int(request.POST.get("novell")),
                defaults={'rate_id': int(request.POST.get('rate'))}
            )
            sum = 0
            nov_rates = Rating.objects.filter(novell=nov)
            for i in nov_rates:
                sum += i.rate.value
            nov.overall_rating = sum / len(nov_rates)
            nov.save(update_fields=['overall_rating'])
            return HttpResponse(status=201)
        else:
            return HttpResponse(status=400)


class AllNewsView(ListView):
    model = Post
    template_name = 'core/post/post_list.html'
    context_object_name = 'posts'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_anonymous:
            self.request.user.user_profile.new_post_check = timezone.now()
            self.request.user.user_profile.save()
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'core/post/post_detail.html'
    context_object_name = 'post'


class JsonFilterNovellsView(ListView):
    template_name = 'core/novells_list.html'
    context_object_name = 'novells'

    def get_queryset(self):
        if self.request.get_host() == 'www.privereda1.ru' or self.request.get_host() == 'privereda1.ru':
            translator = 'Privereda1'
        else:
            translator = 'Oksiji13'

        q = self.request.GET.get('q')
        if q:
            return Novell.objects.filter(rus_title__icontains=q, translator=translator).values("rus_title", "overall_rating", "slug", "poster")

        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        chaptet_min = self.request.GET.get('chapter-min')
        chaptet_max = self.request.GET.get('chapter-max')
        rating = self.request.GET.get('rating')
        novell_status = self.request.GET.get('novell-trans-status')
        preset_query = Novell.objects.filter(translator=translator)
        translate_status = self.request.GET.get('translate-status')


        if chaptet_min:
            preset_query = preset_query.filter(chapter_count__gte=chaptet_min)
        if chaptet_max:
            preset_query = preset_query.filter(chapter_count__lte=chaptet_max)
        if rating:
            upper_limit = Decimal(rating)
            preset_query = preset_query.filter(overall_rating__gte=upper_limit)
        if novell_status != 'None':
            preset_query = preset_query.filter(status=novell_status)
        if translate_status == 'yes':
            preset_query = preset_query.filter(translate_status=True)
        if translate_status == 'no':
            preset_query = preset_query.filter(translate_status=False)

        if genre_filter and year_filter and len(genre_filter) == 1:
            return preset_query.filter(publish__year__in=year_filter, genres__in=genre_filter, translator=translator).values("rus_title",
                                                                                                      "overall_rating",
                                                                                                      "slug",
                                                                                                      "poster")
        elif len(genre_filter) > 1 and year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in preset_query.filter(publish__year__in=year_filter, translator=translator):
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append({
                        "rus_title": i.rus_title, "overall_rating": i.overall_rating, "slug": i.slug,
                        "poster": str(i.poster.url).replace("media/", "")
                    })
            return a
        elif len(genre_filter) > 1 and not year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in preset_query.all():
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append({"rus_title": i.rus_title, "overall_rating": i.overall_rating, "slug": i.slug,
                              "poster": str(i.poster.url).replace("media/", "")})
            return a

        elif not year_filter and not genre_filter:
            return preset_query.all().values("rus_title", "overall_rating", "slug", "poster")
        else:
            return preset_query.filter(
                Q(publish__year__in=year_filter) | Q(genres__in=genre_filter)).distinct().values("rus_title",
                                                                                                 "overall_rating",
                                                                                                 "slug", "poster")

    def get(self, request, *args, **kwargs):
        queryset = list(self.get_queryset())
        for q in queryset:
            q['starsf'] = []
            a = round(q['overall_rating'])
            if abs(a - q['overall_rating']) > Decimal('0.25') and abs(a - q['overall_rating']) < Decimal('0.75'):
                half = True
            else:
                half = False
            for i in range(int(q['overall_rating'])):
                q['starsf'].append(1)
            q['half'] = half
            empty = 5 - len(q['starsf']) - int(half)
            q['empty'] = []
            for i in range(empty):
                q['empty'].append(1)
        #       return JsonResponse(serializer.data)
        return JsonResponse({"novells": queryset}, safe=False)


class NovellListViewApi(views.APIView):

    def get(self, request):
        q = self.request.GET.get('q')
        if q:
            novells = Novell.objects.filter(rus_title__icontains=q)
            serializer = NovellListSerializer(novells, many=True)
            return Response(serializer.data)
        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        if genre_filter and year_filter and len(genre_filter) == 1:
            novells = Novell.objects.filter(publish__year__in=year_filter, genres__in=genre_filter)
        elif len(genre_filter) > 1 and year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.filter(publish__year__in=year_filter):
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            novells = a
        elif len(genre_filter) > 1 and not year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.all():
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            novells = a
        elif not year_filter and not genre_filter:
            novells = Novell.objects.all()
        else:
            novells = Novell.objects.filter(Q(publish__year__in=year_filter) | Q(genres__in=genre_filter)).distinct()
        serializer = NovellListSerializer(novells, many=True)
        return Response(serializer.data)

def views_for_novell(novell, date_filter, start_date, end_date):
    views = ViewNovell.objects.filter(novell = novell)

    if date_filter == 'today':
        views = views.filter(datetime__date__gte=date.today())
    elif date_filter == 'month':
        views = views.filter(datetime__year__gte = datetime.now().year,
                             datetime__month__gte = datetime.now().month)
    elif date_filter == 'arbitrary_period':
        views = views.filter(datetime__range = [start_date, end_date])

    return len(views)

def profit_for_novell(novell, date_filter, start_date, end_date):
    transactions = UserBalanceChange.objects.filter(novell = novell)

    if date_filter == 'today':
        transactions = transactions.filter(datetime__date__gte=date.today())
    elif date_filter == 'month':
        transactions = transactions.filter(datetime__year__gte = datetime.now().year,
                                           datetime__month__gte = datetime.now().month)
    elif date_filter == 'arbitrary_period':
        transactions = transactions.filter(datetime__range = [start_date, end_date])

    total_amount = sum(tr.amount for tr in transactions)
    return total_amount

def get_url_primary(request, q):
    full_path = request.get_full_path()
    
    if request.GET.get(q):
        sep = full_path[full_path.find(q)-1]
        if request.GET.get(q) == '1':
            return full_path.replace(f"{sep}{q}=1", f"{sep}{q}=-1")
        elif request.GET.get(q) == '-1':
            return full_path.replace(f"{sep}{q}=-1", f"{sep}{q}=1")
    else:
        sep = '&' if len(request.GET) > 0 else '?'
        q = f"{sep}{q}=-1"
        return f"{full_path}{q}"

def get_sorted_array(array, value, column):
        if int(value) > 0:
            return sorted(array, key=lambda i: i[column])
        else:
            return sorted(array, key=lambda i: i[column], reverse=True)

def statistic_view(request, *args, **kwargs):
    translator = request.GET.get('translator')
    if translator == 'Privereda1' or translator == 'Oksiji13':
        novells = Novell.objects.filter(translator=translator)
    else:
        novells = Novell.objects.all()

    date_filter = request.GET.get('date')
    res_array = []
    total = {'views': 0, 'profit': 0}

    for novell in novells:
        res = {}
        res["novell"] = novell.rus_title
        res["views"] = views_for_novell(novell, date_filter, request.GET.get('start_date'), request.GET.get('end_date'))
        res["profit"] = profit_for_novell(novell, date_filter, request.GET.get('start_date'), request.GET.get('end_date'))
        res_array.append(res)
        total["views"] += res["views"]
        total["profit"] += res["profit"]

    header_name = {'text': 'Название на русском', 'url_primary': get_url_primary(request, 'sn')}
    header_view = {'text': 'Просмотры', 'url_primary': get_url_primary(request, 'sv')}
    header_profit = {'text': 'Доход', 'url_primary': get_url_primary(request, 'sp')}
    result_headers = [header_name, header_view, header_profit]

    if request.GET.get('sn'):
        res_array = get_sorted_array(res_array, request.GET.get('sn'), 'novell')

    if request.GET.get('sv'):
        res_array = get_sorted_array(res_array, request.GET.get('sv'), 'views')
        
    if request.GET.get('sp'):
        res_array = get_sorted_array(res_array, request.GET.get('sp'), 'profit')

    return render(request, 'admin/statistics/base.html',
            {
                'result': res_array,
                'total': total,
                'result_headers': result_headers,
                'start_date': request.GET.get('start_date'),
                'end_date': request.GET.get('end_date'),
                'translator': request.GET.get('translator'),
                'date': request.GET.get('date')
                }
            ) 

