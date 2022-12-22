from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

NUM_OF_POSTS = 10


def index(request):
    template = 'posts/index.html'
    text = 'Последние изменения на сайте'
    posts = Post.objects.all()
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'text': text,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)

    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = posts.count()
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    follower = author.follower.all()
    count_follower = follower.count()
    user = request.user.username
    paginator = Paginator(posts, NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': posts,
        'author': author,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'count_follower': count_follower,
        'following': following,
        'user': user,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    author = post.author
    posts_autor = Post.objects.filter(author=author)
    posts_count = posts_autor.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'author': author,
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        if request.user.is_authenticated:
            form.instance.author = request.user
            form.save()
            return redirect('posts:profile', username=request.user)
    posts = Post.objects.all()
    context = {
        'form': form,
        'posts': posts,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = get_object_or_404(Post, id=post_id)
    if request.user != is_edit.author:
        return redirect('posts:post_detail', post_id=is_edit.id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=is_edit)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=is_edit.id)
    context = {
        'form': form,
        'is_edit': is_edit,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list_follow = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(post_list_follow, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/follow.html',
                  {'page_obj': page_obj, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    follow = get_object_or_404(User, username=username)

    if request.user.username == username:
        return redirect('posts:profile', username=username)

    Follow.objects.get_or_create(user=request.user, author=follow)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(Follow,
                                 author=get_object_or_404(User,
                                                          username=username),
                                 user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)
