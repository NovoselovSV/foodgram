from django.conf import settings
from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """User model."""

    email = models.EmailField(
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True)
    first_name = models.CharField(max_length=settings.MAX_NAME_LENGTH)
    last_name = models.CharField(max_length=settings.MAX_NAME_LENGTH)
    username = models.CharField(
        max_length=settings.MAX_NAME_LENGTH,
        unique=True,
        validators=(
            UnicodeUsernameValidator(),
        ))
    subscriptions = models.ManyToManyField(
        'self',
        through='Subscription',
        related_name='subscribers',
        verbose_name='Подписки',
        through_fields=('subscription', 'subscriber'),
        symmetrical=False)
    avatar = models.ImageField(upload_to='avatars/',
                               null=True,
                               blank=True,
                               default=None)

    REQUIRED_FIELDS = (
        'email',
        'firstname',
        'lastname',
        'password')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Subscription many to many model."""

    subscription = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='+')
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='+')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='Subscriptions_unique_relationships',
                fields=['subscription', 'subscriber']
            ),
            models.CheckConstraint(
                name='prevent_self_follow',
                check=~models.Q(subscription=models.F('subscriber')),
            ),
        ]
