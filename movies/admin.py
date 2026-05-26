from django import forms
from django.contrib import admin
from django.db import models

from .models import (
    StorageChannel,
    Content,
    ContentItem,
    RequiredLink,
    RequiredLinkClick,
)


@admin.register(StorageChannel)
class StorageChannelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "telegram_chat_id",
        "contents_count_display",
        "items_count_display",
    )

    search_fields = (
        "name",
        "telegram_chat_id",
    )

    readonly_fields = (
        "contents_count_display",
        "items_count_display",
    )

    fields = (
        "name",
        "telegram_chat_id",
        "description",
        "contents_count_display",
        "items_count_display",
    )

    def contents_count_display(self, obj):
        if not obj.pk:
            return 0
        return obj.contents.count()

    contents_count_display.short_description = "Contents count"

    def items_count_display(self, obj):
        if not obj.pk:
            return 0
        return ContentItem.objects.filter(
            content__storage_channel=obj
        ).count()

    items_count_display.short_description = "Content items count"


class ContentItemInline(admin.StackedInline):
    model = ContentItem
    extra = 1

    formfield_overrides = {
        models.TextField: {
            "widget": forms.TextInput(
                attrs={
                    "style": "width: 90%;",
                }
            )
        }
    }

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
        "storage_channel",
        "slug",
        "items_count_display",
    )

    list_filter = (
        "content_type",
        "storage_channel",
    )

    search_fields = (
        "title",
        "slug",
        "storage_channel__name",
    )

    fields = (
        "title",
        "content_type",
        "storage_channel",
        "slug",
    )

    inlines = [
        ContentItemInline,
    ]

    def items_count_display(self, obj):
        return obj.items.count()

    items_count_display.short_description = "Items count"


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content",
        "content_storage_channel",
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
        "content__storage_channel__name",
    )

    list_filter = (
        "content",
        "content__storage_channel",
        "quality",
    )

    readonly_fields = (
        "storage_chat_id",
        "storage_message_id",
        "download_code",
        "deep_link",
        "created_at",
    )

    formfield_overrides = {
        models.TextField: {
            "widget": forms.TextInput(
                attrs={
                    "style": "width: 90%;",
                }
            )
        }
    }

    def content_storage_channel(self, obj):
        return obj.content.storage_channel

    content_storage_channel.short_description = "Storage channel"

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