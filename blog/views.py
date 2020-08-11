from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from django.views.generic import ListView
from taggit.models import Tag
from django.db.models import Count

from .models import Post
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', 'body')
            # search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
                # similarity=TrigramSimilarity('title', query)
            ).filter(search=search_query).order_by('-rank')

    return render(request, 'blog/post_search.html',
                  {'form': form,
                   'query': query,
                   'results': results})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            print(data)
            # send email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'\
                .format(data['name'], data['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'\
                .format(post.title, post_url, data['name'], data['comments'])

            try:
                send_mail(subject, message, data['email'], [data['to']])
                sent = True
            except Exception as ex:
                print(ex)

    else:
        form = EmailPostForm()
    return render(request, 'blog/post_share.html', {'post': post, 'form': form, 'sent': sent})


class PostList(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post_list.html'


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/post_list.html',
                  {'page': page, 'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day
                             )
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        print(comment_form)
        if comment_form.is_valid():
            # create comment object bu don't save it yet
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post_detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form,
                   'similar_posts': similar_posts
                   })
