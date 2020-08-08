from django.urls import path
from . import views as v

app_name = 'blog'

urlpatterns = [
    path('', v.PostList.as_view(), name='post_list'),
    path('<int:post_id>/share', v.post_share, name='post_share'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>', v.post_detail, name='post_detail')
]