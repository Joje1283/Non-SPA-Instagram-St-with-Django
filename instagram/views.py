from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from instagram.forms import PostForm, CommentForm
from instagram.models import Tag, Post


@login_required
def index(request):
    post_qs = Post.objects.all()
    post_qs = post_qs.filter(
        Q(author=request.user) |
        Q(author__in=request.user.following_set.all())
    )
    timesince = timezone.now() - timedelta(days=3)
    post_qs = post_qs.filter(created_at__gte=timesince)  # grater than equal
    suggested_user_list = get_user_model().objects.all()
    suggested_user_list = suggested_user_list.exclude(pk=request.user.pk)
    suggested_user_list = suggested_user_list.exclude(pk__in=request.user.following_set.all())[:3]
    comment_form = CommentForm()
    return render(request, "instagram/index.html", {
        'post_list': post_qs,
        'suggested_user_list': suggested_user_list,
        'comment_form': comment_form
    })


@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            post.tag_set.add(*post.extract_tag_list())  # 실제 PK가 있어야 하므로 post를 저장후에 수행한다.
            messages.success(request, '포스팅을 저장했습니다.')
            return redirect(post)
    else:
        form = PostForm()
    return render(request, 'instagram/post_form.html', {
        'form': form,
    })


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comment_form = CommentForm()
    return render(request, 'instagram/post_detail.html', {
        'post': post,
        'comment_form': comment_form,
    })


@login_required
def post_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.like_user_set.add(request.user)
    messages.success(request, f'포스팅 #{post.pk}를 좋아합니다.')
    redirect_url = request.META.get('HTTP_REFERER', 'root')
    return redirect(redirect_url)


@login_required
def comment_new(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if request.is_ajax():
                return render(request, "instagram/_comment.html", {
                    "comment": comment
                })
            return redirect(comment.post)
    else:
        form = CommentForm()
    return render(request, 'instagram/comment_form.html', {
        'form': form,
    })


@login_required
def post_unlike(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.like_user_set.remove(request.user)
    messages.success(request, f'포스팅 #{post.pk}의 좋아요를 취소합니다.')
    redirect_url = request.META.get('HTTP_REFERER', 'root')
    return redirect(redirect_url)


def user_page(request, username):
    page_user = get_object_or_404(get_user_model(), username=username, is_active=True)

    if request.user.is_authenticated:
        is_follow = request.user.following_set.filter(pk=page_user.pk).exists()
    else:
        is_follow = False

    post_list = Post.objects.filter(author=page_user)
    post_list_count = post_list.count()  # 실제 데이터베이스에 count 쿼리를 던지게 됩니다.
    return render(request, 'instagram/user_page.html', {
        'page_user': page_user,
        'post_list': post_list,
        'post_list_count': post_list_count,
        'is_follow': is_follow,
    })
