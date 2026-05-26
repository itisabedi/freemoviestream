from django.contrib import admin
from .models import Content, ContentItem, RequiredLink, RequiredLinkClick


class ContentItemInline(admin.StackedInline):
    model = ContentItem
    extra = 1

    readonly_fields = (
        "storage_chat_id",
        "storage_message_id",
        "download_code",
        "deep_link",
        "created_at",
    )

    fields = (
        "title",
        ("season_number", "episode_number", "quality"),
        "telegram_message_link",
        ("storage_chat_id", "storage_message_id"),
        "download_code",
        "deep_link",
        "created_at",
    )

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "content_type",
        "slug",
    )

    list_filter = (
        "content_type",
    )

    search_fields = (
        "title",
        "slug",
    )

    inlines = [
        ContentItemInline,
    ]


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content",
        "title",
        "season_number",
        "episode_number",
        "quality",
        "download_code",
        "storage_chat_id",
        "storage_message_id",
        "created_at",
    )

    search_fields = (
        "title",
        "download_code",
        "telegram_message_link",
        "content__title",
    )

    list_filter = (
        "content",
        "quality",
    )

    readonly_fields = (
        "storage_chat_id",
        "storage_message_id",
        "download_code",
        "deep_link",
        "created_at",
    )

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "content",
                "title",
                "season_number",
                "episode_number",
                "quality",
                "telegram_message_link",
            )

        return (
            "content",
            "title",
            "season_number",
            "episode_number",
            "quality",
            "telegram_message_link",
            "storage_chat_id",
            "storage_message_id",
            "download_code",
            "deep_link",
            "created_at",
        )


@admin.register(RequiredLink)
class RequiredLinkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "url",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)
    search_fields = ("title", "url")


@admin.register(RequiredLinkClick)
class RequiredLinkClickAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "telegram_user_id",
        "item_code",
        "required_link",
        "is_opened",
        "created_at",
        "opened_at",
    )

    list_filter = ("is_opened", "required_link")
    search_fields = ("telegram_user_id", "item_code", "token")
    readonly_fields = ("token", "created_at", "opened_at")