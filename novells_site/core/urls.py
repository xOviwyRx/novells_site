from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='home'),
    path('<slug:slug>', views.NovellDetailView.as_view(), name='novell_detail'),
    path('<str:slug>/chapter/<int:number>', views.ChapterDetailView.as_view(), name='chapter_detail'),
]
