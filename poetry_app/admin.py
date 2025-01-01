from django.contrib import admin
from .models import News, DailyPrompt, Tag, Poetry, EducationalResource, LearningPath, UserRole, ReportedContent, Profile, Badge

admin.site.register(News)
admin.site.register(DailyPrompt)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)

@admin.register(Poetry)
class PoetryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at')
    search_fields = ('title', 'body', 'author__username')
    list_filter = ('status', 'tags')

@admin.register(EducationalResource)
class EducationalResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'resource_type', 'topic', 'created_at')
    search_fields = ('title', 'description', 'topic__name')
    list_filter = ('resource_type', 'topic')

@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'created_at')
    search_fields = ('title',)
    filter_horizontal = ('poems', 'resources')

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'parent')
    search_fields = ('user__username', 'role')

@admin.register(ReportedContent)
class ReportedContentAdmin(admin.ModelAdmin):
    list_display = ('poem', 'reporter', 'reason', 'is_resolved', 'reported_at')
    search_fields = ('poem__title', 'reporter__username', 'reason')
    list_filter = ('reason', 'is_resolved')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode', 'hide_followers', 'font_size')
    search_fields = ('user__username',)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)