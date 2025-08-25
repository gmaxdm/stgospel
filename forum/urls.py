from django.urls import path
from forum import views


urlpatterns = [
    path('', views.index, name='forum-index'),

    # json
    path('posts/', views.posts, name='forum-topic-posts'),
    path('post/like/', views.post_like, name="forum-post-like"),
    path('post/delete/', views.post_delete, name="forum-post-delete"),
    path('post/edit/', views.post_edit, name='forum-topic-post'),

    path('images/upload/', views.upload_img, name='forum-image-upload'),
    path('newtopic/', views.new_topic, name='forum-topic-new'),
    path('<slug:slug>/', views.forum, name='forum-view'),
    path('<slug:slug>/<slug:topic_slug>/', views.topic, name='forum-topic'),
    #path('<slug:slug>/<slug:topic_slug>/close/', views.close_topic, name='forum-topic-close'),
]
