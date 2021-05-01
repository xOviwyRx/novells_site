from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views
from .models import Comment, LikeDislike, Chapter

app_name = 'core'

urlpatterns = [

    path('add_comment/to_chapter/<int:pk>', views.AddComment.as_view(model=Chapter), name='add_comment'),
    path('', views.index, name='home'),
    path('novells_list/', views.NovellListView.as_view(), name='novell_list'),
    path('novells_list/filter/', views.FilterNovellsView.as_view(), name='filter'),

    path('add-rating/', views.AddNovellRating.as_view(), name='add_rating'),

    #path('novells_list/json-filter/', views.JsonFilterNovellsView.as_view(), name='json_filter'),

    path('novell/<slug:slug>', views.NovellDetailView.as_view(), name='novell_detail'),
    path('profile/<int:pk>/<slug:slug>/', views.ProfileDetail.as_view(), name='profile_detail'),
    path('profile/edit/<int:pk>/<slug:slug>/', views.EditMyProfile.as_view(), name='edit_profile'),

    path('<str:slug>/chapter/<int:number>', views.ChapterDetailView.as_view(), name='chapter_detail'),

    path('api/comment/<int:id>/like/',
         login_required(views.VotesView.as_view(model=Comment, vote_type=LikeDislike.LIKE)),
         name='comment_like'),
    path('api/comment/<int:id>/dislike/',
         login_required(views.VotesView.as_view(model=Comment, vote_type=LikeDislike.DISLIKE)),
         name='comment_dislike'),


    path('add_to_bookmark/novell/<int:pk>', views.add_to_bookmark, name='add_to_bookmarks'),
    path('delete_from_bookmark/novell/<int:pk>/<str:frommm>', views.del_from_bookmark, name='del_from_bookmarks'),

]
