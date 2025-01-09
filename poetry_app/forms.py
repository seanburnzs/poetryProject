from django import forms
from .models import Poetry, Tag, Profile, Comment, Folder, Message, Conversation, DailyPrompt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django_summernote.widgets import SummernoteWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field, HTML
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_file_size(file):
    max_size_kb = 2048  # 2MB
    if file.size > max_size_kb * 1024:
        raise ValidationError(f'File too large. Size should not exceed {max_size_kb} KB.')
    
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class PoetryForm(forms.ModelForm):
    show_daily_prompt = forms.BooleanField(
        required=False,
        label='Show Daily Prompt',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select-multiple form-control'}),
        required=False,
        label='Tags',
        help_text='Select existing tags or add new ones.'
    )

    class Meta:
        model = Poetry
        fields = ['title', 'body', 'anonymous', 'status', 'allow_comments', 'tags', 'show_daily_prompt']
        labels = {
            'anonymous': 'Anonymous',
            'allow_comments': 'Allow Comments'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': SummernoteWidget(attrs={'class': 'form-control'}),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select w-auto'}),
            'tags': forms.SelectMultiple(attrs={'class': 'select-multiple form-control'}),
        }

    def __init__(self, *args, **kwargs):
        is_edit = kwargs.pop('is_edit', False)
        super(PoetryForm, self).__init__(*args, **kwargs)

        # Initialize Crispy Forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'title',
            'body',
            'anonymous',
            'allow_comments',
            'status',
            Field('tags', css_class='select-multiple'),  # Ensures Select2 initialization
            'show_daily_prompt',
            Submit('submit', 'Submit Poem', css_class='btn btn-primary')
        )

        if is_edit:
            # Remove 'show_daily_prompt' field when editing
            if 'show_daily_prompt' in self.fields:
                del self.fields['show_daily_prompt']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4, 
                'cols': 40, 
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'd-none'}),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            validate_file_size(picture)
        return picture

    def save(self, commit=True):
        """SAVE PFP."""
        profile = super().save(commit=False)
        if 'profile_picture' in self.files:
            profile.profile_picture = self.files['profile_picture']
        if commit:
            profile.save()
        return profile

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)


class AdvancedSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Keyword')
    author = forms.CharField(required=False)
    tag = forms.ModelChoiceField(queryset=Tag.objects.all(), required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    sort_by = forms.ChoiceField(required=False, choices=[
        ('date', 'Date'),
        ('likes', 'Likes'),
        ('comments', 'Comments'),
    ])

    def __init__(self, *args, **kwargs):
        super(AdvancedSearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.add_input(Submit('submit', 'Search'))

class PreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['hide_followers', 'font_size']
        widgets = {
            'hide_followers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'font_size': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'hide_followers': 'Hide Followers and Following Lists',
            'font_size': 'Font Size',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }

class UserSearchForm(forms.Form):
    query = forms.CharField(
        label='',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by username',
            'class': 'form-control',
        })
    )

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'poems']
        widgets = {
            'poems': forms.CheckboxSelectMultiple(),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message...'}),
        }

class NewConversationForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Recipient",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message...'}),
        label="Message"
    )
    
class AddToFolderForm(forms.Form):
    folder = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Folder",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_folder_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'New Folder Name', 'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        super(AddToFolderForm, self).__init__(*args, **kwargs)
        self.fields['folder'].queryset = Folder.objects.filter(user=user)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'folder',
            HTML('<p class="text-center my-2">OR</p>'),
            'new_folder_name',
            Submit('submit', 'Add to Folder', css_class='btn btn-theme-primary')
        )