from django.conf import settings
from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """User model."""

    email = models.EmailField(
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True)
    first_name = models.CharField(max_length=settings.MAX_USERS_NAMES_LENGTH)
    last_name = models.CharField(max_length=settings.MAX_USERS_NAMES_LENGTH)
    username = models.CharField(
        max_length=settings.MAX_USERS_NAMES_LENGTH,
        unique=True,
        validators=(
            UnicodeUsernameValidator(),
        ))
    subscriptions = models.ManyToManyField(
        'self',
        through='Subscription',
        related_name='subscribers',
        verbose_name='Подписки',
        through_fields=('subscriber', 'subscription'),
        symmetrical=False)
    avatar = models.ImageField(upload_to='users/',
                               null=True,
                               blank=True,
                               default=None)

    REQUIRED_FIELDS = (
        'email',
        'first_name',
        'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Subscription many to many model."""

    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Подписан на')
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name='subscriptions_unique_relationships',
                fields=['subscription', 'subscriber']
            ),
            models.CheckConstraint(
                name='prevent_self_follow',
                check=~models.Q(subscription=models.F('subscriber')),
            ),
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscription}'


class Ingredient(models.Model):
    """Model for ingredients."""

    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=settings.MAX_INGREGIENTS_NAME)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=settings.MAX_MEASUREMENT_NAME)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} в {self.measurement_unit}'


class Tag(models.Model):
    """Model for tag."""

    name = models.CharField(
        verbose_name='Название',
        unique=True,
        max_length=settings.MAX_TAGS_NAME)
    slug = models.SlugField(
        verbose_name='Уникальное название на латинице',
        unique=True,
        max_length=settings.MAX_TAGS_NAME)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name
