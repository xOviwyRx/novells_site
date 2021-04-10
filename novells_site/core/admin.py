from django.contrib import admin
from .models import Genre, Novell, Chapter, Comment, LikeDislike, Profile


# Register your models here.

@admin.register(Novell)
class NovellAdmin(admin.ModelAdmin):
    list_display = ('original_title', 'author', 'status', 'description')
    prepopulated_fields = {'slug': ('original_title',)}


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'status', 'novell')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('title', 'description',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('chapter',)


@admin.register(LikeDislike)
class LikeDisLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'vote', 'user', 'content_type', 'object_id', 'content_object')
    list_filter = ('user',)
    list_display_links = ('id',)
    list_editable = ('vote',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name',)

