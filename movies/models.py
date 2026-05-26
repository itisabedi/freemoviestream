import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


BOT_USERNAME = "your_movie_download_bot"


class Content(models.Model):
    TYPE_SERIES = "series"
    TYPE_MOVIE = "movie"

    CONTENT_TYPES = [
        (TYPE_SERIES, "Series"),
        (TYPE_MOVIE, "Movie"),
    ]

    title = models.CharField(max_length=255)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        default=TYPE_SERIES,
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContentItem(models.Model):
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name="items"
    )

    title = models.CharField(max_length=255)

    season_number = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    episode_number = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    quality = models.CharField(
        max_length=50,
        blank=True
    )

    telegram_message_link = models.TextField()

    storage_chat_id = models.BigIntegerField(blank=True, null=True)
    storage_message_id = models.BigIntegerField(blank=True, null=True)

    download_code = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )

    deep_link = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["content", "season_number", "episode_number", "quality"]

    def parse_telegram_message_link(self):
        match = re.search(r"t\.me/c/(\d+)/(\d+)", self.telegram_message_link or "")

        if not match:
            raise ValidationError(
                "Telegram link is invalid. Example: https://t.me/c/3936259652/2"
            )

        channel_id = match.group(1)
        message_id = match.group(2)

        self.storage_chat_id = int(f"-100{channel_id}")
        self.storage_message_id = int(message_id)

    def generate_download_code(self):
        parts = [self.content.slug]

        if self.season_number:
            parts.append(f"S{self.season_number:02d}")

        if self.episode_number:
            parts.append(f"E{self.episode_number:02d}")

        if self.quality:
            parts.append(self.quality.upper())

        self.download_code = "_".join(parts)

    def generate_deep_link(self):
        self.deep_link = f"https://t.me/{BOT_USERNAME}?start={self.download_code}"

    def clean(self):
        self.parse_telegram_message_link()
        self.generate_download_code()
        self.generate_deep_link()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content.title} - {self.title}"


class RequiredLink(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class RequiredLinkClick(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    telegram_user_id = models.BigIntegerField()
    item_code = models.CharField(max_length=255)

    required_link = models.ForeignKey(
        RequiredLink,
        on_delete=models.CASCADE,
        related_name="clicks"
    )

    is_opened = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.telegram_user_id} - {self.required_link.title}"