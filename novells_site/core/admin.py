from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Genre, Novell, Chapter, Comment, LikeDislike, Profile, Rating, RatingStar, Slider, Post, Review, \
    UserBalanceChange, NovellArch


# Register your models here.

@admin.register(Novell)
class NovellAdmin(admin.ModelAdmin):
    list_display = ('rus_title', 'author', 'status', 'views', 'overall_rating', 'translate_status')
    filter_horizontal = ('genres',)
    prepopulated_fields = {'slug': ('eng_title',)}
    readonly_fields = ('overall_rating',)
    list_editable = ('translate_status',)
    list_filter = ('translator',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'status', 'novell')
    exclude = ('publish',)
    list_filter = ('novell', 'status',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('title', 'description',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'body', 'content_object')


@admin.register(LikeDislike)
class LikeDisLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'vote', 'user', 'content_type', 'object_id', 'content_object')
    list_filter = ('user',)
    list_display_links = ('id',)
    list_editable = ('vote',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'name_id')
    filter_horizontal = ('bookmarks', 'planned', 'readed', 'in_process_reading', 'chapter_readed', 'buyed_chapters')


@admin.register(RatingStar)
class RatingStarAdmin(admin.ModelAdmin):
    list_display = ('value',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('author', 'rate', 'novell')


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('shot_img', 'position', 'active',)

    def shot_img(self, obj):
        return mark_safe('<img src={} width="210" height="90"/>'.format(obj.shot.url))

    shot_img.short_description = 'Изображение'


admin.site.register(Post)

admin.site.register(Review)

admin.site.register(UserBalanceChange)

admin.site.register(NovellArch)
