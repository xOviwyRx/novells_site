from django.contrib import admin
from .models import Genre, Novell, Chapter


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
