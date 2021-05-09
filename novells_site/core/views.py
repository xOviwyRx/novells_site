import json

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import login_required

from .models import Novell, Chapter, LikeDislike, Profile, Genre, Rating, Slider, Post, Review, RatingStar
from .forms import CommentForm, EditProfileForm, RatingForm
from django.http import HttpResponse, JsonResponse


# Create your views here.
class GenreYear:

    def get_genres(self):
        return Genre.objects.all()

    def get_year(self):
        return Novell.objects.all().order_by('publish__year').values_list('publish__year').distinct()


def index(request):
    pop_novell = Novell.objects.filter(important=True)
    # pop_novell = Novell.objects.order_by('-views').first()
    test = pop_novell.first()
    shedule_chapter = Chapter.objects.all().order_by('-created')[:8]
    all_novells = Novell.objects.all()
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
        if not self.request.user.is_anonymous:
            self.request.user.user_profile.chapter_readed.add(
                get_object_or_404(Chapter, novell=nov, number=self.kwargs['number']))
        return get_object_or_404(Chapter, novell=nov, number=self.kwargs['number'])


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


@login_required
def add_to_bookmark(request, pk, type_of):
    nov = get_object_or_404(Novell, pk=pk)
    if type_of == 'bookmark':
        request.user.user_profile.bookmarks.add(nov)
    if type_of == 'planned':
        request.user.user_profile.planned.add(nov)
    elif type_of == 'readed':
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
    elif type_of == 'readed':
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


class PostDetailView(DetailView):
    model = Post
    template_name = 'core/post/post_detail.html'
    context_object_name = 'post'


"""
class JsonFilterNovellsView(ListView):
    template_name = 'core/novells_list.html'
    context_object_name = 'novells'

    def get_queryset(self):
        genre_filter = self.request.GET.getlist('genre')
        year_filter = self.request.GET.getlist('year')
        if genre_filter and year_filter and len(genre_filter) == 1:
            return Novell.objects.filter(publish__year__in=year_filter, genres__in=genre_filter).values('slug','original_title', 'poster')
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

    def get(self, request, *args, **kwargs):
        queryset = list(self.get_queryset())
        return JsonResponse({"novells": queryset}, safe=False)

"""
