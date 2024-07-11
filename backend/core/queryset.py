from django.db import models
from django.db.models import Exists, OuterRef

from . import models as project_models


class AddOptionsQuerySet(models.QuerySet):
    """Queryset for additional options while evaluting query."""

    def add_is_subscribed_annotate(
            self,
            potential_subscriber_id,
            subscription_id_field):
        return self.annotate(
            is_subscribed=Exists(
                project_models.Subscription.objects.filter(
                    subscriber_id=potential_subscriber_id,
                    subscription_id=OuterRef('pk'))))
