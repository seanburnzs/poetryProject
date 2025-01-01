import django_filters
from django.contrib.auth.models import User
from .models import Poetry, Tag
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class PoetryFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Title Contains'
    )
    body = django_filters.CharFilter(
        field_name='body',
        lookup_expr='icontains',
        label='Body Contains'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=Tag.objects.all(),
        widget=django_filters.widgets.CSVWidget,
        label='Tags'
    )
    author = django_filters.ModelChoiceFilter(
        field_name='author',
        queryset=User.objects.all(),
        label='Author'
    )
    created_at = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Date Range'
    )
    min_likes = django_filters.NumberFilter(
        field_name='likes__count',
        lookup_expr='gte',
        label='Minimum Likes'
    )
    max_likes = django_filters.NumberFilter(
        field_name='likes__count',
        lookup_expr='lte',
        label='Maximum Likes'
    )
    min_comments = django_filters.NumberFilter(
        field_name='comments__count',
        lookup_expr='gte',
        label='Minimum Comments'
    )
    max_comments = django_filters.NumberFilter(
        field_name='comments__count',
        lookup_expr='lte',
        label='Maximum Comments'
    )
    
    class Meta:
        model = Poetry
        fields = [
            'title',
            'body',
            'tags',
            'author',
            'created_at',
            'min_likes',
            'max_likes',
            'min_comments',
            'max_comments'
        ]
        widgets = {
            'created_at': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(PoetryFilter, self).__init__(*args, **kwargs)
        self.form.helper = FormHelper()
        self.form.helper.form_method = 'get'
        self.form.helper.add_input(Submit('submit', 'Search'))
