import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import (
    PoetryForm, ProfileUpdateForm, CommentForm, PreferencesForm, NewConversationForm,
    CustomUserCreationForm, UserSearchForm, FolderForm, MessageForm, AdvancedSearchForm, AddToFolderForm
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
import random
from django.utils import timezone
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Count, Q, Exists, OuterRef
from datetime import timedelta
from .models import (
    FavoritePoem, Poetry, Tag, Following, Comment, Badge, EducationalResource, LearningPath,
    News, DailyPrompt, Notification, Folder, Message, Conversation, PoemReaction
)
import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
logger = logging.getLogger(__name__)
from collections import defaultdict
from django.views.generic import ListView, DetailView
from django.db import IntegrityError

def index(request):
    # Featured Poem
    featured_poem = Poetry.objects.filter(status='published').order_by('?').first()

    news_messages = News.objects.filter(is_active=True).order_by('-created_at')

    today = timezone.now().date()
    daily_prompt = DailyPrompt.objects.filter(date=today).first()

    # Latest Poems (replace Count('likes') with Count of 'reactions' filtered for 'like')
    poems = Poetry.objects.filter(status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')[:10]

    favorite_poem_ids = []
    if request.user.is_authenticated:
        favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)

    # Prepare absolute URLs for poems
    for poem in poems:
        poem.absolute_url = request.build_absolute_uri(reverse('poetry_app:view_poem', args=[poem.id]))

    return render(request, 'poetry_app/index.html', {
        'featured_poem': featured_poem,
        'poems': poems,
        'favorite_poem_ids': favorite_poem_ids,
        'news_messages': news_messages,
        'daily_prompt': daily_prompt,
    })


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}!')
            return redirect('poetry_app:discover')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'poetry_app/register.html', {'form': form})


@login_required
def submit_poetry(request):
    daily_prompt = None
    if request.method == 'POST':
        # Extract submitted tag names and IDs
        submitted_tags = request.POST.getlist('tags')  # This includes both tag IDs and new tag names
        logger.debug(f"Submitted tags: {submitted_tags}")

        # Separate existing tags (numeric IDs) from new tags (strings)
        existing_tag_ids = [tag for tag in submitted_tags if tag.isdigit()]
        new_tag_names = [tag for tag in submitted_tags if not tag.isdigit()]
        logger.debug(f"Existing tag IDs: {existing_tag_ids}")
        logger.debug(f"New tag names: {new_tag_names}")

        # Fetch existing Tag objects
        existing_tags = Tag.objects.filter(id__in=existing_tag_ids)
        logger.debug(f"Existing tags fetched: {[tag.name for tag in existing_tags]}")

        # Create new Tag objects for any new tags
        new_tags = []
        for tag_name in new_tag_names:
            tag_obj, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                logger.debug(f"Created new tag: {tag_obj.name}")
            new_tags.append(tag_obj)
        logger.debug(f"All tags (existing + new): {[tag.name for tag in existing_tags | Tag.objects.filter(id__in=[tag.id for tag in new_tags])]}")
        
        # Combine existing and new Tag objects
        all_tags = list(existing_tags) + list(new_tags)

        # Replace 'tags' in POST data with list of existing tag IDs
        post_data = request.POST.copy()
        post_data.setlist('tags', [tag.id for tag in all_tags])

        # Initialize the form with modified POST data
        form = PoetryForm(post_data, request.FILES)

        if form.is_valid():
            if form.cleaned_data.get('show_daily_prompt'):
                # Get today's prompt
                today = timezone.now().date()
                daily_prompt = DailyPrompt.objects.filter(date=today).first()
            else:
                poetry = form.save(commit=False)
                poetry.author = request.user
                poetry.save()
                form.save_m2m()  # Save tags

                # Set all tags (existing and new)
                poetry.tags.set(all_tags)

                messages.success(request, "Your poem has been submitted.")

                # Award 'First Poem' badge
                poems_count = Poetry.objects.filter(author=request.user, status='published').count()
                if poems_count == 1:
                    badge, created = Badge.objects.get_or_create(
                        name='First Poem',
                        defaults={'description': 'Published your first poem'}
                    )
                    request.user.profile.badges.add(badge)

                return redirect('poetry_app:user_profile', username=request.user.username)
        else:
            logger.error(f"Form is invalid: {form.errors}")
            # Form errors will be displayed in the template
    else:
        form = PoetryForm()

    # Get today's prompt if not already fetched
    if daily_prompt is None:
        today = timezone.now().date()
        daily_prompt = DailyPrompt.objects.filter(date=today).first()

    return render(request, 'poetry_app/submit_poetry.html', {'form': form, 'daily_prompt': daily_prompt})


@login_required
def delete_poem(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)

    if poem.author != request.user:
        messages.error(request, "You do not have permission to delete this poem.")
        return redirect('poetry_app:discover')

    if request.method == 'POST':
        poem.delete()
        messages.success(request, "Poem deleted successfully.")
        return redirect(reverse('poetry_app:user_profile', args=[request.user.username]))

    return render(request, 'poetry_app/confirm_delete.html', {'poem': poem})


@login_required
def my_poems(request):
    # My Creations
    poems = Poetry.objects.filter(author=request.user).annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-updated_at')
    drafts = poems.filter(status='draft')
    published = poems.filter(status='published')

    # My Favorites
    favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
    favorite_poems = Poetry.objects.filter(id__in=favorite_poem_ids).annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )

    # My Likes
    liked_poem_ids = PoemReaction.objects.filter(user=request.user, reaction_type='like').values_list('poem_id', flat=True)
    liked_poems = Poetry.objects.filter(id__in=liked_poem_ids).annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )

    return render(request, 'poetry_app/my_poems.html', {
        'drafts': drafts,
        'published': published,
        'favorite_poems': favorite_poems,
        'liked_poems': liked_poems,
        'favorite_poem_ids': favorite_poem_ids,
        'liked_poem_ids': liked_poem_ids,
    })


@login_required
def user_profile(request, username):
    # Get the user object based on the username
    profile_user = get_object_or_404(User, username=username)

    # Determine if the current user is viewing their own profile
    is_own_profile = (profile_user == request.user)

    # Fetch all poems authored by profile_user
    poems = Poetry.objects.filter(author=profile_user).annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')

    # Separate drafts and published poems
    if is_own_profile:
        # Include all poems, including anonymous ones
        drafts = poems.filter(status='draft')
        published = poems.filter(status='published')
    else:
        # Exclude anonymous poems when viewing someone else's profile
        drafts = Poetry.objects.none()
        published = poems.filter(status='published', anonymous=False)

    # Fetch favorite poems (only if viewing own profile)
    if is_own_profile:
        favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
        favorite_poems = Poetry.objects.filter(id__in=favorite_poem_ids).annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        ).order_by('-created_at')

        # Fetch folders
        folders = Folder.objects.filter(user=request.user).prefetch_related('poems')
    else:
        favorite_poems = None
        folders = None
        favorite_poem_ids = []

    # Fetch liked poems using PoemReaction
    liked_poem_ids = (PoemReaction.objects.filter(user=request.user, reaction_type='like')
                      .values_list('poem_id', flat=True) if request.user.is_authenticated else [])
    liked_poems = Poetry.objects.filter(id__in=liked_poem_ids).annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')

    # Determine if the current user is following the profile user
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Following.objects.filter(follower=request.user, following=profile_user).exists()

    # Get user reactions
    user_reactions = {}
    user_reactions_list = defaultdict(list)
    if request.user.is_authenticated:
        reactions = PoemReaction.objects.filter(user=request.user)
        user_reactions = {reaction.poem_id: reaction.reaction_type for reaction in reactions}
        for reaction in reactions:
            user_reactions_list[reaction.poem_id].append(reaction.reaction_type)

    # Define reaction icons
    reaction_icons = {
        'insightful': 'fas fa-lightbulb text-warning',
        'beautiful': 'fas fa-feather text-primary',
        'inspiring': 'fas fa-sun text-success',
        'sad': 'fas fa-sad-tear text-info',
        'funny': 'fas fa-laugh text-warning',
        'thoughtful': 'fas fa-brain text-secondary',
        'uplifting': 'fas fa-smile-beam text-success',
    }

    context = {
        'profile_user': profile_user,
        'drafts': drafts,
        'published': published,
        'favorite_poems': favorite_poems,
        'liked_poems': liked_poems,
        'folders': folders,
        'is_following': is_following,
        'favorite_poem_ids': favorite_poem_ids,
        'liked_poem_ids': liked_poem_ids,
        'user_reactions': user_reactions,
        'user_reactions_list': user_reactions_list,
        'reaction_icons': reaction_icons,
        'is_own_profile': is_own_profile,
    }

    return render(request, 'poetry_app/user_profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('poetry_app:user_profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'poetry_app/edit_profile.html', {'form': form})


@login_required
def unfavorite_poem(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)
    FavoritePoem.objects.filter(user=request.user, poem=poem).delete()
    messages.success(request, 'Poem removed from favorites.')
    return redirect('poetry_app:user_profile', username=request.user.username)


@login_required
def remove_saved(request, saved_poem_id):
    saved_poem = get_object_or_404(FavoritePoem, id=saved_poem_id, user=request.user)
    saved_poem.delete()
    messages.success(request, 'Poem removed from favorites.')
    return redirect('poetry_app:favorites')


def featured_poem(request):
    poem = Poetry.objects.filter(status='published').order_by('?').first()
    return render(request, 'poetry_app/featured_poem.html', {'poem': poem})


def filter_by_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    poems = Poetry.objects.filter(tags=tag, status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')
    return render(request, 'poetry_app/read.html', {'poems': poems, 'tag': tag})


def for_you(request):
    if request.user.is_authenticated:
        user_tags = request.user.profile.favorite_tags.all()
        favorite_poets = request.user.profile.favorite_poets.all()
        poems = (Poetry.objects.filter(
            Q(tags__in=user_tags) | Q(author__in=favorite_poets),
            status='published'
        )
        .distinct()
        .annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        )
        .order_by('-created_at'))
    else:
        poems = Poetry.objects.none()
    return render(request, 'poetry_app/for_you.html', {'poems': poems})


def explore(request):
    all_poems = Poetry.objects.filter(status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )
    random_poems = all_poems.order_by('?')[:5] if all_poems.exists() else []
    return render(request, 'poetry_app/explore.html', {'random_poems': random_poems})


@login_required
def read_poems(request):
    # Fetch user reactions
    user_reactions = {}
    user_reactions_list = defaultdict(list)
    if request.user.is_authenticated:
        reactions = PoemReaction.objects.filter(user=request.user)
        user_reactions = {reaction.poem_id: reaction.reaction_type for reaction in reactions}
        for reaction in reactions:
            user_reactions_list[reaction.poem_id].append(reaction.reaction_type)

    # Initialize querysets for all tabs (replace Count('likes') with Count of 'reactions' filtered for 'like')
    explore_poems = Poetry.objects.filter(status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )

    following_poems = Poetry.objects.none()
    friends_poems = Poetry.objects.none()

    if request.user.is_authenticated:
        # Fetch users the current user is following
        following_users = request.user.following_set.values_list('following', flat=True)

        # Poems by followed users
        following_poems = Poetry.objects.filter(
            author__in=following_users,
            status='published'
        ).annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        )

        # Define 'friends' as mutual followers
        friends = User.objects.filter(
            following_set__follower=request.user
        ).filter(
            followers_set__following=request.user
        ).distinct()

        # Debug: Print friends' usernames
        print(f"Friends: {[user.username for user in friends]}")

        # Poems by friends
        friends_poems = Poetry.objects.filter(
            author__in=friends,
            status='published'
        ).annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        )

        # Debug: Print friends' poems
        print(f"Friends' Poems: {[poem.title for poem in friends_poems]}")

        # Fetch liked and favorite poems IDs
        favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
        liked_poem_ids = PoemReaction.objects.filter(user=request.user, reaction_type='like').values_list('poem_id', flat=True)
    else:
        favorite_poem_ids = []
        liked_poem_ids = []

    # Handle Advanced Search Filters
    form = AdvancedSearchForm(request.GET or None)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        author = form.cleaned_data.get('author')
        tag = form.cleaned_data.get('tag')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        sort_by = form.cleaned_data.get('sort_by')

        if query:
            explore_poems = explore_poems.filter(Q(title__icontains=query) | Q(body__icontains=query))
            following_poems = following_poems.filter(Q(title__icontains=query) | Q(body__icontains=query))
            friends_poems = friends_poems.filter(Q(title__icontains=query) | Q(body__icontains=query))

        if author:
            explore_poems = explore_poems.filter(author__username__icontains=author)
            following_poems = following_poems.filter(author__username__icontains=author)
            friends_poems = friends_poems.filter(author__username__icontains=author)

        if tag:
            explore_poems = explore_poems.filter(tags=tag)
            following_poems = following_poems.filter(tags=tag)
            friends_poems = friends_poems.filter(tags=tag)

        if date_from:
            explore_poems = explore_poems.filter(created_at__gte=date_from)
            following_poems = following_poems.filter(created_at__gte=date_from)
            friends_poems = friends_poems.filter(created_at__gte=date_from)

        if date_to:
            explore_poems = explore_poems.filter(created_at__lte=date_to)
            following_poems = following_poems.filter(created_at__lte=date_to)
            friends_poems = friends_poems.filter(created_at__lte=date_to)

        if sort_by:
            # For 'likes', use num_likes=Count('reactions', filter=Q(reactions__reaction_type='like'))
            if sort_by == 'date':
                explore_poems = explore_poems.order_by('-created_at')
                following_poems = following_poems.order_by('-created_at')
                friends_poems = friends_poems.order_by('-created_at')
            elif sort_by == 'likes':
                explore_poems = explore_poems.annotate(
                    num_likes=Count('reactions', filter=Q(reactions__reaction_type='like'))
                ).order_by('-num_likes')

                following_poems = following_poems.annotate(
                    num_likes=Count('reactions', filter=Q(reactions__reaction_type='like'))
                ).order_by('-num_likes')

                friends_poems = friends_poems.annotate(
                    num_likes=Count('reactions', filter=Q(reactions__reaction_type='like'))
                ).order_by('-num_likes')

            elif sort_by == 'comments':
                explore_poems = explore_poems.annotate(num_comments=Count('comments')).order_by('-num_comments')
                following_poems = following_poems.annotate(num_comments=Count('comments')).order_by('-num_comments')
                friends_poems = friends_poems.annotate(num_comments=Count('comments')).order_by('-num_comments')

    # Limit the number of poems per tab for performance
    explore_poems = explore_poems[:20]
    if request.user.is_authenticated:
        following_poems = following_poems[:20]
        friends_poems = friends_poems[:20]

    reaction_icons = {
        'insightful': 'fas fa-lightbulb text-warning',
        'beautiful': 'fas fa-feather text-primary',
        'inspiring': 'fas fa-sun text-success',
        'sad': 'fas fa-sad-tear text-info',
        'funny': 'fas fa-laugh text-warning',
        'thoughtful': 'fas fa-brain text-secondary',
        'uplifting': 'fas fa-smile-beam text-success',
    }

    context = {
        'explore_poems': explore_poems,
        'following_poems': following_poems,
        'friends_poems': friends_poems,
        'form': form,
        'favorite_poem_ids': favorite_poem_ids,
        'liked_poem_ids': liked_poem_ids,
        'user_reactions': user_reactions,
        'user_reactions_list': user_reactions_list,
        'reaction_icons': reaction_icons,
    }

    return render(request, 'poetry_app/read.html', context)


@login_required
def preferences(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = PreferencesForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated.')
            return redirect('poetry_app:preferences')
        else:
            # Print form errors for debugging
            print(form.errors)
            messages.error(request, 'Error updating preferences.')
    else:
        form = PreferencesForm(instance=profile)

    return render(request, 'poetry_app/preferences.html', {'form': form})


@login_required
def favorites(request):
    # Get the IDs of poems favorited by the user
    favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
    # Fetch the actual poem objects, now annotated properly
    poems = Poetry.objects.filter(id__in=favorite_poem_ids, status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')

    context = {
        'poems': poems,
        'favorite_poem_ids': favorite_poem_ids,
    }
    return render(request, 'poetry_app/favorites.html', context)


@login_required
def edit_poem(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)

    if poem.author != request.user:
        messages.error(request, "You don't have permission to edit this poem.")
        return redirect('poetry_app:discover')

    if request.method == 'POST':
        form = PoetryForm(request.POST, request.FILES, instance=poem, is_edit=True)
        if form.is_valid():
            form.save()
            messages.success(request, "Poem updated successfully.")
            return redirect(reverse('poetry_app:user_profile', args=[request.user.username]))
    else:
        form = PoetryForm(instance=poem, is_edit=True)

    return render(request, 'poetry_app/edit_poem.html', {'form': form, 'poem': poem})


@login_required
def report_poem(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)

    if request.method == 'POST':
        send_mail(
            'Poem Reported',
            f'The poem "{poem.title}" has been reported by {request.user.username}.',
            settings.DEFAULT_FROM_EMAIL,
            ['admin@example.com'],
            fail_silently=False,
        )
        messages.success(request, "Poem reported successfully.")
        return redirect('poetry_app:discover')

    return render(request, 'poetry_app/report_poem.html', {'poem': poem})


@login_required
def save_poem(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)
    FavoritePoem.objects.get_or_create(user=request.user, poem=poem)
    messages.success(request, 'Poem added to favorites.')
    return redirect('poetry_app:view_poem', poem_id=poem.id)


from django.db.models import Count, Q

@login_required
def view_poem(request, poem_id):
    # Annotate the Poetry object with likes_count
    poem = get_object_or_404(
        Poetry.objects.annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        ),
        id=poem_id,
        status='published'
    )
    
    # Fetch favorite and liked poem IDs for the current user
    favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
    liked_poem_ids = PoemReaction.objects.filter(user=request.user, reaction_type='like').values_list('poem_id', flat=True)

    # Handle comments submission
    if poem.allow_comments:
        if request.method == 'POST':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                parent_id = request.POST.get('parent_id')
                parent_comment = Comment.objects.filter(id=parent_id).first() if parent_id else None
                comment = comment_form.save(commit=False)
                comment.poem = poem
                comment.user = request.user
                comment.parent = parent_comment
                comment.save()
                
                # Create Notification if enabled
                if settings.NOTIFICATIONS_ENABLED:
                    Notification.objects.create(
                        user=poem.author,
                        actor=request.user,
                        notification_type='comment',
                        poem=poem,
                        comment=comment
                    )
                
                messages.success(request, "Your comment has been added.")
                return redirect('poetry_app:view_poem', poem_id=poem.id)
        else:
            comment_form = CommentForm()
    else:
        comment_form = None

    # Fetch top-level comments and their replies
    comments = poem.comments.filter(parent__isnull=True).select_related('user').prefetch_related('replies__user')

    # Determine if the user has liked or favorited the poem
    has_liked = poem.id in liked_poem_ids
    has_favorited = poem.id in favorite_poem_ids

    # Construct absolute URL for sharing
    absolute_url = request.build_absolute_uri(reverse('poetry_app:view_poem', args=[poem.id]))

    # Prepare user reactions for the current poem
    user_reactions_list = {}
    if request.user.is_authenticated:
        reactions = PoemReaction.objects.filter(user=request.user, poem=poem)
        user_reactions_list[poem.id] = [reaction.reaction_type for reaction in reactions]

    # Define reaction icons mapping
    reaction_icons = {
        'insightful': 'fas fa-lightbulb text-warning',
        'beautiful': 'fas fa-feather text-primary',
        'inspiring': 'fas fa-sun text-success',
        'sad': 'fas fa-sad-tear text-info',
        'funny': 'fas fa-laugh text-warning',
        'thoughtful': 'fas fa-brain text-secondary',
        'uplifting': 'fas fa-smile-beam text-success',
    }

    # Build the context for the template
    context = {
        'poem': poem,
        'favorite_poem_ids': favorite_poem_ids,
        'liked_poem_ids': liked_poem_ids,
        'comments': comments,
        'comment_form': comment_form,
        'has_liked': has_liked,
        'has_favorited': has_favorited,
        'absolute_url': absolute_url,
        'user_reactions_list': user_reactions_list,
        'reaction_icons': reaction_icons,
    }

    return render(request, 'poetry_app/view_poem.html', context)

def reply_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, pk=comment_id)
    poem = parent_comment.poem

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.user = request.user
            reply.poem = poem
            reply.parent = parent_comment
            reply.save()
            return redirect('poetry_app:view_poem', poem_id=poem.id)
    else:
        form = CommentForm()

    return render(request, 'poetry_app/reply_comment.html', {
        'form': form,
        'parent_comment': parent_comment,
    })


@login_required
def personalized_content(request):
    profile = request.user.profile
    favorite_tags = profile.favorite_tags.all()
    favorite_poets = profile.favorite_poets.all()

    poems = (Poetry.objects.filter(
        Q(tags__in=favorite_tags) | Q(author__in=favorite_poets),
        status='published'
    )
    .distinct()
    .annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )
    .order_by('-created_at')[:10])

    favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)

    return render(request, 'poetry_app/personalized_content.html', {
        'poems': poems,
        'favorite_poem_ids': favorite_poem_ids,
    })


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        messages.error(request, "You cannot follow yourself.")
        return redirect('poetry_app:user_profile', username=username)

    already_following = Following.objects.filter(follower=request.user, following=user_to_follow).exists()
    if already_following:
        messages.info(request, f"You are already following {username}.")
    else:
        Following.objects.create(follower=request.user, following=user_to_follow)
        messages.success(request, f"You are now following {username}!")
        if settings.NOTIFICATIONS_ENABLED:
            Notification.objects.create(
                user=user_to_follow,
                actor=request.user,
                notification_type='follow'
            )

    return redirect('poetry_app:user_profile', username=username)


@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)

    if user_to_unfollow == request.user:
        messages.error(request, "You cannot unfollow yourself.")
        return redirect('poetry_app:user_profile', username=username)

    following = Following.objects.filter(follower=request.user, following=user_to_unfollow)
    if following.exists():
        following.delete()
        messages.success(request, f"You have unfollowed {username}.")
    else:
        messages.info(request, f"You are not following {username}.")

    return redirect('poetry_app:user_profile', username=username)


def advanced_search(request):
    poems = Poetry.objects.filter(status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    )
    form = AdvancedSearchForm(request.GET or None)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        author = form.cleaned_data.get('author')
        tag = form.cleaned_data.get('tag')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        sort_by = form.cleaned_data.get('sort_by')

        if query:
            poems = poems.filter(Q(title__icontains=query) | Q(body__icontains=query))
        if author:
            poems = poems.filter(author__username__icontains=author)
        if tag:
            poems = poems.filter(tags=tag)
        if date_from:
            poems = poems.filter(created_at__gte=date_from)
        if date_to:
            poems = poems.filter(created_at__lte=date_to)
        if sort_by:
            if sort_by == 'date':
                poems = poems.order_by('-created_at')
            elif sort_by == 'likes':
                poems = poems.annotate(
                    num_likes=Count('reactions', filter=Q(reactions__reaction_type='like'))
                ).order_by('-num_likes')
            elif sort_by == 'comments':
                poems = poems.annotate(num_comments=Count('comments')).order_by('-num_comments')
    else:
        poems = poems.order_by('-created_at')

    paginator = Paginator(poems, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'poems': page_obj,
        'form': form,
    }
    return render(request, 'poetry_app/advanced_search.html', context)


def autocomplete_title(request):
    if 'term' in request.GET:
        search_term = request.GET.get('term')
        poems = Poetry.objects.filter(title__icontains=search_term)
        titles = list(poems.values_list('title', flat=True))
        return JsonResponse(titles, safe=False)
    return JsonResponse([], safe=False)


def autocomplete_body(request):
    if 'term' in request.GET:
        search_term = request.GET.get('term')
        poems = Poetry.objects.filter(body__icontains=search_term)
        poem_bodies = list(poems.values_list('body', flat=True)[:10])
        return JsonResponse(poem_bodies, safe=False)
    return JsonResponse([], safe=False)


@login_required
@require_POST
def toggle_like_ajax(request, poem_id):
    try:
        poem = get_object_or_404(Poetry, id=poem_id)
        existing_reaction = PoemReaction.objects.filter(
            user=request.user,
            poem=poem,
            reaction_type='like'
        ).first()

        liked = False
        if existing_reaction:
            existing_reaction.delete()
        else:
            PoemReaction.objects.create(
                user=request.user, 
                poem=poem, 
                reaction_type='like'
            )
            liked = True

        # Return total likes from DB
        like_count = PoemReaction.objects.filter(
            poem=poem, 
            reaction_type='like'
        ).count()

        return JsonResponse({'liked': liked, 'like_count': like_count})
    except Exception as e:
        logger.exception("Error toggling like.")
        return JsonResponse({'error': 'An error occurred.'}, status=500)

@login_required
def toggle_favorite_ajax(request, poem_id):
    if request.method == 'POST':
        poem = get_object_or_404(Poetry, id=poem_id)
        favorited, created = FavoritePoem.objects.get_or_create(user=request.user, poem=poem)

        if not created:
            # Already favorited, so unfavorite
            favorited.delete()
            return JsonResponse({'favorited': False})
        else:
            # If newly favorited
            if settings.NOTIFICATIONS_ENABLED:
                Notification.objects.create(
                    user=poem.author,
                    actor=request.user,
                    notification_type='favorite',
                    poem=poem
                )
            return JsonResponse({'favorited': True})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)


@login_required
@require_POST
def toggle_dark_mode(request):
    profile = request.user.profile
    profile.dark_mode = not profile.dark_mode
    profile.save()
    return JsonResponse({'dark_mode': profile.dark_mode})


@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    if user.profile.hide_followers and user != request.user:
        messages.error(request, "This user's followers list is hidden.")
        return redirect('poetry_app:user_profile', username=username)
    followers = user.followers_set.select_related('follower')
    context = {
        'profile_user': user,
        'followers': followers,
    }
    return render(request, 'poetry_app/followers_list.html', context)


@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)
    if user.profile.hide_followers and user != request.user:
        messages.error(request, "This user's following list is hidden.")
        return redirect('poetry_app:user_profile', username=username)
    following = user.following_set.select_related('following')
    context = {
        'profile_user': user,
        'following': following,
    }
    return render(request, 'poetry_app/following_list.html', context)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    poem_id = comment.poem.id
    comment.delete()
    messages.success(request, "Your comment has been deleted.")
    return redirect('poetry_app:view_poem', poem_id=poem_id)


@login_required
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    messages.success(request, "The comment has been reported.")
    return redirect('poetry_app:view_poem', poem_id=comment.poem.id)


def search_users(request):
    query = ''
    results = []
    followed_users = []

    if request.user.is_authenticated:
        followed_users = request.user.following_set.values_list('following__username', flat=True)

    if 'query' in request.GET:
        form = UserSearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = User.objects.filter(username__icontains=query)
    else:
        form = UserSearchForm()

    context = {
        'form': form,
        'query': query,
        'results': results,
        'followed_users': followed_users,
    }
    return render(request, 'poetry_app/search_results.html', context)


@login_required
def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            form.save_m2m()
            messages.success(request, 'Folder created successfully.')
            return redirect('poetry_app:user_profile', username=request.user.username)
    else:
        form = FolderForm()
    return render(request, 'poetry_app/create_folder.html', {'form': form})


@login_required
def notifications(request):
    if not settings.NOTIFICATIONS_ENABLED:
        messages.info(request, "Notifications are currently disabled.")
        return redirect('poetry_app:discover')
    notifications = request.user.notifications.all()
    return render(request, 'poetry_app/notifications.html', {'notifications': notifications})


@login_required
def add_to_folder(request, poem_id):
    poem = get_object_or_404(Poetry, id=poem_id)
    if request.method == 'POST':
        form = AddToFolderForm(request.user, request.POST)
        if form.is_valid():
            folder = form.cleaned_data.get('folder')
            new_folder_name = form.cleaned_data.get('new_folder_name')
            if folder:
                folder.poems.add(poem)
                messages.success(request, f'Poem "{poem.title}" added to folder "{folder.name}".')
            elif new_folder_name:
                # Create a new folder and add the poem to it
                new_folder, created = Folder.objects.get_or_create(user=request.user, name=new_folder_name)
                new_folder.poems.add(poem)
                messages.success(request, f'Poem "{poem.title}" added to new folder "{new_folder.name}".')
            else:
                messages.error(request, 'Please select a folder or enter a new folder name.')
                return render(request, 'poetry_app/add_to_folder.html', {'form': form, 'poem': poem})
            return redirect('poetry_app:user_profile', username=request.user.username)
    else:
        form = AddToFolderForm(request.user)
    return render(request, 'poetry_app/add_to_folder.html', {'form': form, 'poem': poem})


@login_required
def delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    if request.method == 'POST':
        folder.delete()
        messages.success(request, 'Folder deleted successfully.')
        return redirect('poetry_app:user_profile', username=request.user.username)
    else:
        return render(request, 'poetry_app/confirm_delete_folder.html', {'folder': folder})


@login_required
def remove_from_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    if request.method == 'POST':
        poem_id = request.POST.get('poem_id')
        poem = get_object_or_404(Poetry, id=poem_id)
        folder.poems.remove(poem)
        messages.success(request, f'Poem "{poem.title}" removed from folder "{folder.name}".')
        return redirect('poetry_app:user_profile', username=request.user.username)
    else:
        messages.error(request, 'Invalid request.')
        return redirect('poetry_app:user_profile', username=request.user.username)


@login_required
def conversations_list(request):
    """
    Display a list of all conversations the user is part of.
    """
    conversations = request.user.conversations.all().order_by('-last_updated')
    return render(request, 'poetry_app/conversations_list.html', {'conversations': conversations})


@login_required
def conversation_detail(request, conversation_id):
    """
    Display all messages within a specific conversation and handle sending new messages.
    Annotate each message with like and favorite counts, and whether the current user has liked or favorited it.
    """
    # Retrieve the conversation or return 404 if not found
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Check if the current user is a participant in the conversation
    if request.user not in conversation.participants.all():
        django_messages.error(request, "You do not have permission to view this conversation.")
        return redirect('poetry_app:conversations_list')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.timestamp = timezone.now()
            message.save()

            conversation.last_updated = timezone.now()
            conversation.save()

            return redirect('poetry_app:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    # Mark all messages as read (exclude user's own)
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    # Annotate messages with like/favorite counts
    messages_qs = conversation.messages.filter(is_deleted=False).annotate(
        like_count=Count('reactions', filter=Q(reactions__reaction='like')),
        favorite_count=Count('reactions', filter=Q(reactions__reaction='favorite')),
        user_has_liked=Exists(
            PoemReaction.objects.filter(
                message=OuterRef('pk'),
                reaction='like',
                user=request.user
            )
        ),
        user_has_favorited=Exists(
            PoemReaction.objects.filter(
                message=OuterRef('pk'),
                reaction='favorite',
                user=request.user
            )
        )
    ).order_by('timestamp')

    context = {
        'conversation': conversation,
        'messages': messages_qs,
        'form': form,
        'user': request.user,
    }

    return render(request, 'poetry_app/conversation_detail.html', context)


@login_required
def start_conversation(request):
    """
    Initiate a new conversation or redirect to an existing one.
    """
    if request.method == 'POST':
        form = NewConversationForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data['recipient']
            body = form.cleaned_data['body']
            # Check if a conversation already exists between the users
            conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
            if not conversation:
                conversation = Conversation.objects.create(last_updated=timezone.now())
                conversation.participants.add(request.user, recipient)
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body,
                timestamp=timezone.now()
            )
            conversation.last_updated = timezone.now()
            conversation.save()
            django_messages.success(request, 'Conversation started successfully.')
            return redirect('poetry_app:conversation_detail', conversation_id=conversation.id)
    else:
        form = NewConversationForm()
    return render(request, 'poetry_app/start_conversation.html', {'form': form})


@login_required
@require_POST
def unsend_message(request):
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        if not message_id:
            logger.error("No message_id provided in unsend_message.")
            return JsonResponse({'status': 'error', 'message': 'No message_id provided.'}, status=400)

        message = get_object_or_404(Message, id=message_id, sender=request.user)
        message.is_deleted = True
        message.save()
        logger.info(f"Message {message_id} marked as deleted by user {request.user}.")

        conversation_id = message.conversation.id
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{conversation_id}',
            {
                'type': 'unsend_message',
                'message_id': message_id
            }
        )
        logger.info(f"Unsend notification sent for message {message_id} in conversation {conversation_id}.")

        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in unsend_message request body.")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        logger.exception("Exception in unsend_message view.")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def add_reaction(request, poem_id):
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')

        if not reaction_type:
            return JsonResponse({'error': "No 'reaction_type' provided."}, status=400)

        # Exclude 'like' from valid reactions, as it's handled by toggle_like_ajax
        valid_reactions = [
            'insightful', 'beautiful', 'inspiring',
            'sad', 'funny', 'thoughtful', 'uplifting'
        ]
        if reaction_type not in valid_reactions:
            return JsonResponse({'error': "Invalid 'reaction_type'."}, status=400)

        poem = get_object_or_404(Poetry, id=poem_id)

        existing_reaction = PoemReaction.objects.filter(
            user=request.user,
            poem=poem,
            reaction_type=reaction_type
        ).first()

        if existing_reaction:
            existing_reaction.delete()
        else:
            PoemReaction.objects.create(
                user=request.user,
                poem=poem,
                reaction_type=reaction_type
            )

        current_reactions = list(
            PoemReaction.objects.filter(
                user=request.user,
                poem=poem
            ).values_list('reaction_type', flat=True)
        )

        return JsonResponse({
            'status': 'success',
            'current_reactions': current_reactions
        })
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in request body.")
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Poetry.DoesNotExist:
        logger.exception("Poetry does not exist.")
        return JsonResponse({'error': 'Poem not found.'}, status=404)
    except Exception as e:
        logger.exception("Unhandled exception in add_reaction.")
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def add_reaction_to_poem(request, poem_id):
    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')

        if not reaction_type:
            return JsonResponse({'error': "No 'reaction_type' provided."}, status=400)

        valid_reactions = [
            'insightful', 'beautiful', 'inspiring',
            'sad', 'funny', 'thoughtful', 'uplifting'
        ]
        if reaction_type not in valid_reactions:
            return JsonResponse({'error': "Invalid 'reaction_type'."}, status=400)

        poem = get_object_or_404(Poetry, id=poem_id)

        existing_reaction = PoemReaction.objects.filter(
            user=request.user,
            poem=poem,
            reaction_type=reaction_type
        ).first()

        if existing_reaction:
            existing_reaction.delete()
        else:
            PoemReaction.objects.create(
                user=request.user,
                poem=poem,
                reaction_type=reaction_type
            )

        current_reactions = list(
            PoemReaction.objects.filter(
                user=request.user,
                poem=poem
            ).values_list('reaction_type', flat=True)
        )

        return JsonResponse({
            'status': 'success',
            'current_reactions': current_reactions
        })
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in request body.")
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Poetry.DoesNotExist:
        logger.exception("Poetry does not exist.")
        return JsonResponse({'error': 'Poem not found.'}, status=404)
    except Exception as e:
        logger.exception("Unhandled exception in add_reaction_to_poem.")
        return JsonResponse({'error': str(e)}, status=400)


class EducationListView(ListView):
    model = Tag
    template_name = 'poetry_app/education_list.html'
    context_object_name = 'tags'

    def get_queryset(self):
        return Tag.objects.filter(category='Topic')


class EducationDetailView(DetailView):
    model = Tag
    template_name = 'poetry_app/education_detail.html'
    context_object_name = 'tag'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = EducationalResource.objects.filter(topic=self.object)
        context['poems'] = self.object.poems.filter(status='published')
        return context


class LearningPathListView(ListView):
    model = LearningPath
    template_name = 'poetry_app/learning_path_list.html'
    context_object_name = 'learning_paths'


@login_required
def discover(request):
    news_messages = News.objects.filter(is_active=True)
    daily_prompt = DailyPrompt.objects.filter(date=timezone.now().date()).first()
    # Replace old Count('likes') with filtered Count('reactions')
    explore_poems = Poetry.objects.filter(status='published').annotate(
        likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
        comments_count=Count('comments')
    ).order_by('-created_at')[:20]

    if request.user.is_authenticated:
        following_users = request.user.following_set.values_list('following', flat=True)
        following_poems = Poetry.objects.filter(author__in=following_users, status='published').annotate(
            likes_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
            comments_count=Count('comments')
        ).order_by('-created_at')[:20]

        for poem in explore_poems:
            print(f"Poem ID: {poem.id}, Title: '{poem.title}', Likes Count: {poem.likes_count}")

        friends_poems = Poetry.objects.none()  # Placeholder

        favorite_poem_ids = FavoritePoem.objects.filter(user=request.user).values_list('poem_id', flat=True)
        liked_poem_ids = PoemReaction.objects.filter(user=request.user, reaction_type='like').values_list('poem_id', flat=True)

        user_reactions = PoemReaction.objects.filter(user=request.user).values('poem_id', 'reaction_type')
        user_reactions_list = defaultdict(list)
        for reaction in user_reactions:
            user_reactions_list[reaction['poem_id']].append(reaction['reaction_type'])

        reaction_icons = {
            'insightful': 'fas fa-lightbulb text-warning',
            'beautiful': 'fas fa-feather text-primary',
            'inspiring': 'fas fa-sun text-success',
            'sad': 'fas fa-sad-tear text-info',
            'funny': 'fas fa-laugh text-warning',
            'thoughtful': 'fas fa-brain text-secondary',
            'uplifting': 'fas fa-smile-beam text-success',
        }
    else:
        following_poems = Poetry.objects.none()
        friends_poems = Poetry.objects.none()
        favorite_poem_ids = []
        liked_poem_ids = []
        user_reactions_list = {}
        reaction_icons = {}

    context = {
        'news_messages': news_messages,
        'daily_prompt': daily_prompt,
        'explore_poems': explore_poems,
        'following_poems': following_poems,
        'friends_poems': friends_poems,
        'favorite_poem_ids': favorite_poem_ids,
        'liked_poem_ids': liked_poem_ids,
        'user_reactions_list': user_reactions_list,
        'reaction_icons': reaction_icons,
    }
    return render(request, 'poetry_app/discover.html', context)


def learn(request):
    query = request.GET.get('q', '')
    if query:
        topics_list = Tag.objects.filter(Q(category='Topic') & Q(name__icontains=query))
    else:
        topics_list = Tag.objects.filter(category='Topic')

    paginator = Paginator(topics_list, 9)
    page_number = request.GET.get('page')
    topics = paginator.get_page(page_number)

    context = {
        'topics': topics,
        'query': query,
    }
    return render(request, 'poetry_app/learn.html', context)
