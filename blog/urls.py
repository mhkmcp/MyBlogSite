from django.urls import path
from . import views as v
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    # path('', v.PostList.as_view(), name='post_list'),
    path('', v.post_list, name='post_list'),
    path('tag/<slug:tag_slug>', v.post_list, name='post_list_by_tag'),
    path('<int:post_id>/share', v.post_share, name='post_share'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>', v.post_detail, name='post_detail'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', v.post_search, name='post_search'),
]