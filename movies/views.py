from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models import RequiredLinkClick


def redirect_required_link(request, token):
    click = get_object_or_404(RequiredLinkClick, token=token)

    if not click.is_opened:
        click.is_opened = True
        click.opened_at = timezone.now()
        click.save(update_fields=["is_opened", "opened_at"])

    return redirect(click.required_link.url)