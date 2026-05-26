from django.urls import path

from .views import redirect_required_link


urlpatterns = [
    path("r/<uuid:token>/", redirect_required_link, name="redirect_required_link"),
]