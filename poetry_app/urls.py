from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib import admin
from . import views
from django.conf import settings

app_name = 'poetry_app'

urlpatterns = [    
    # Home and Authentication
    path('', views.discover, name='discover'),
    path('register/', views.register, name='register'),

    # Poetry Management
    path('submit/', views.submit_poetry, name='submit_poetry'),
    path('delete/<int:poem_id>/', views.delete_poem, name='delete_poem'),
    path('edit/<int:poem_id>/', views.edit_poem, name='edit_poem'),
    path('report/<int:poem_id>/', views.report_poem, name='report_poem'),
    path('poem/<int:poem_id>/', views.view_poem, name='view_poem'),

    # User Poems and Favorites
    path('favorites/', views.favorites, name='favorites'),
    path('favorites/remove/<int:saved_poem_id>/', views.remove_saved, name='remove_saved'),
    path('poem/save/<int:poem_id>/', views.save_poem, name='save_poem'),
    path('toggle_favorite_ajax/<int:poem_id>/', views.toggle_favorite_ajax, name='toggle_favorite_ajax'),

    # Profile Management
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/unfavorite/<int:poem_id>/', views.unfavorite_poem, name='unfavorite_poem'),

    # Social Features
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),

    # Additional Features
    path('preferences/', views.preferences, name='preferences'),
    
    # Likes
    path('toggle_like_ajax/<int:poem_id>/', views.toggle_like_ajax, name='toggle_like_ajax'),
    
    # Dark/Light mode
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    
    # Followers and Following Lists
    path('user/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('user/<str:username>/following/', views.following_list, name='following_list'),
    
    # Comments
    path('comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comment/report/<int:comment_id>/', views.report_comment, name='report_comment'),
    
    # Search
    path('search/', views.search_users, name='search_users'),
  
    # Folders
    path('folders/create/', views.create_folder, name='create_folder'),
    path('poem/<int:poem_id>/add_to_folder/', views.add_to_folder, name='add_to_folder'),
    path('folders/<int:folder_id>/delete/', views.delete_folder, name='delete_folder'),
    path('folders/<int:folder_id>/remove_poem/', views.remove_from_folder, name='remove_from_folder'),
    
    #Messages
    path('messages/', views.conversations_list, name='conversations_list'),
    path('messages/start/', views.start_conversation, name='start_conversation'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/unsend/', views.unsend_message, name='unsend_message'),
    path('add_reaction/', views.add_reaction, name='add_reaction'),
        
    # Reactions
    path('poem/<int:poem_id>/add_reaction/', views.add_reaction_to_poem, name='add_reaction_to_poem'),

    # S3 direct upload
    path('force_upload_test/', views.force_upload_test, name='force_upload_test'),
]

if settings.NOTIFICATIONS_ENABLED:
    urlpatterns += [
        path('notifications/', views.notifications, name='notifications'),
    ]