import json
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required

from .models import Novell, Chapter, LikeDislike, Profile, Genre, Rating, Slider, Post, Review, RatingStar, Comment
from .forms import CommentForm, EditProfileForm, RatingForm
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from rest_framework import viewsets, filters, views
from rest_framework.response import Response
from .serializers import NovellListSerializer


# Create your views here.

def js_filter_test(request):
    return render(request, 'core/novells_list_new.html')


class GenreYear:

    def get_genres(self):
        return Genre.objects.all()

    def get_year(self):
        return Novell.objects.all().order_by('publish__year').values_list('publish__year').distinct()

    def get_status(self):
        return Novell.objects.all().values_list('status').distinct()


def index(request):
    pop_novell = Novell.objects.filter(important=True)
    # pop_novell = Novell.objects.order_by('-views').first()
    test = pop_novell.first()
    shedule_chapter = Chapter.objects.all().order_by('-created')[:8]
    all_novells = Novell.objects.filter().order_by('-views')[:6]
    shots = Slider.objects.filter(active=True).order_by('position')

    return render(request, 'core/home.html', {'pops': pop_novell,
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
        nov = get_object_or_404(Novell, slug=self.kwargs['slug'])
        chapter = get_object_or_404(Chapter, novell=nov, number=self.kwargs['number'])
        #
        if not self.request.user.is_anonymous:
            self.request.user.user_profile.chapter_readed.add(chapter)

        if not chapter.premium:
            return chapter

        if chapter.premium and self.request.user.is_anonymous:
            # "Вы пытаетесь открыть платную главу. Войдите в аккаунт, где она куплена, или купите её!"
            raise PermissionDenied
        elif self.request.user.is_anonymous and chapter.premium and chapter not in self.request.user.user_profile.buyed_chapters.all():
            # "Вы пытаетесь открыть платную главу. Купите её, это не так дорого!"
            raise PermissionDenied
        elif not self.request.user.is_anonymous and chapter.premium and chapter in self.request.user.user_profile.buyed_chapters.all():
            return chapter
        else:
            raise Http404('Неизвестная ошибка')


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
        for i in request.POST.getlist('chosen'):
            chapter = get_object_or_404(Chapter, id=i)
            request.user.user_profile.buyed_chapters.add(chapter)
        return redirect(n.get_absolute_url())
    else:
        return HttpResponse('Недостаточно средств или сбой системы')


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
        if q:
            return Novell.objects.filter(rus_title__icontains=q)
        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        if genre_filter and year_filter and len(genre_filter) == 1:
            return Novell.objects.filter(publish__year__in=year_filter, genres__in=genre_filter)
        elif len(genre_filter) > 1 and year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.filter(publish__year__in=year_filter):
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            return a
        elif len(genre_filter) > 1 and not year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in Novell.objects.all():
                if set(genres_in_filter) <= set(i.genres.all()):
                    a.append(i)
            return a
        elif not year_filter and not genre_filter:
            return Novell.objects.all()
        else:
            return Novell.objects.filter(Q(publish__year__in=year_filter) | Q(genres__in=genre_filter)).distinct()
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
        q = self.request.GET.get('q')
        if q:
            return Novell.objects.filter(rus_title__icontains=q).values("rus_title", "overall_rating", "slug", "poster")

        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        chaptet_min = self.request.GET.get('chapter-min')
        chaptet_max = self.request.GET.get('chapter-max')
        rating = self.request.GET.get('rating')
        novell_status = self.request.GET.get('novell-trans-status')
        preset_query = Novell.objects.all()
        translate_status = self.request.GET.get('translate-status')

        print(translate_status)

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
            return preset_query.filter(publish__year__in=year_filter, genres__in=genre_filter).values("rus_title",
                                                                                                      "overall_rating",
                                                                                                      "slug",
                                                                                                      "poster")
        elif len(genre_filter) > 1 and year_filter:
            genres_in_filter = [Genre.objects.get(id=i) for i in genre_filter]
            a = []
            for i in preset_query.filter(publish__year__in=year_filter):
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
