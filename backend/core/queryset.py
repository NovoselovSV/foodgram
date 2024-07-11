from django.db import models
from django.db.models import Exists, OuterRef

from . import models as project_models


class AddOptionsUserQuerySet(models.QuerySet):
    """Queryset for additional options while making query with User model."""

    def add_is_subscribed_annotate(self, potential_subscriber_id):
        return self.annotate(
            is_subscribed=Exists(
                project_models.Subscription.objects.filter(
                    subscriber_id=potential_subscriber_id,
                    subscription_id=OuterRef('pk'))))


class AddOptionsRecipeQuerySet(models.QuerySet):
    """Queryset for additional options while making query with Recipe model."""

    def add_is_favorited_annotate(self, user_id):
        return self.annotate(
            is_favorited=Exists(
                project_models.UserRecipeFavorite.objects.filter(
                    recipe_id=OuterRef('pk'),
                    user_id=user_id)))
