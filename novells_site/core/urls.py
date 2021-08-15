from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views
from .models import Comment, LikeDislike, Chapter, Post, Review


app_name = 'core'

urlpatterns = [

    path('add_comment/to_chapter/<int:pk>', views.AddComment.as_view(model=Chapter), name='add_comment_to_chapter'),
    path('add_comment/to_post/<int:pk>', views.AddComment.as_view(model=Post), name='add_comment_to_post'),
    # path(''),
    path('', views.index, name='home'),
    path('novells_list/', views.NovellListView.as_view(), name='novell_list'),
    path('novells_list/filter/', views.FilterNovellsView.as_view(), name='filter'),
    path('news/', views.AllNewsView.as_view(), name='all_news'),
    path('new/<int:pk>/<slug:slug>', views.PostDetailView.as_view(), name='post_detail'),

    path('add-rating/', views.AddNovellRating.as_view(), name='add_rating'),

    path('novells_list/json-filter/', views.JsonFilterNovellsView.as_view(), name='json_filter'),

    path('novell/<slug:slug>', views.NovellDetailView.as_view(), name='novell_detail'),
    path('profile/<int:pk>/<slug:slug>/', views.ProfileDetail.as_view(), name='profile_detail'),
    path('profile/edit/<int:pk>/<slug:slug>/', views.EditMyProfile.as_view(), name='edit_profile'),

    path('<str:slug>/chapter/<int:number>', views.ChapterDetailView.as_view(), name='chapter_detail'),

    path('api/get_notifications/', login_required(views.GetNotificationView.as_view()), name='get_notifications'),
    path('api/get_news/', login_required(views.GetNotificationNewsView.as_view()), name='get_news'),
    path('api/check_notifications/', login_required(views.CheckNotificationView.as_view()),
         name='check_notifications_all'),

    path('api/comment/<int:id>/like/',
         login_required(views.VotesView.as_view(model=Comment, vote_type=LikeDislike.LIKE)),
         name='comment_like'),
    path('api/comment/<int:id>/dislike/',
         login_required(views.VotesView.as_view(model=Comment, vote_type=LikeDislike.DISLIKE)),
         name='comment_dislike'),

    path('api/review/<int:id>/like/',
         login_required(views.VotesView.as_view(model=Review, vote_type=LikeDislike.LIKE)),
         name='comment_like'),
    path('api/review/<int:id>/dislike/',
         login_required(views.VotesView.as_view(model=Review, vote_type=LikeDislike.DISLIKE)),
         name='comment_dislike'),

    #  Добавление-удаление из закладок(избранного/запланированного)
    path('add_to_bookmark/novell/<int:pk>/<str:type_of>', views.add_to_bookmark, name='add_to_bookmarks'),
    path('delete_from_bookmark/novell/<int:pk>/<str:type_of>/<str:frommm>', views.del_from_bookmark,
         name='del_from_bookmarks'),


    path('novell_filter_test/', views.js_filter_test),
    path('api/nov_list/', views.NovellListViewApi.as_view()),

    path('buying_chapter/<int:pk>/', views.buy_chapter, name='buy_chapter'),

    path('buying_many_chapters/<int:pk>/', views.buy_many_chapters, name='buying_many_chapters'),

]
