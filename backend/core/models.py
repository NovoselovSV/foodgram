from django.conf import settings
from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models


from .queryset import AddOptionsUserQuerySet, AddOptionsRecipeQuerySet


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
                               verbose_name='Аватар',
                               null=True,
                               blank=True,
                               default=None)
    favorites = models.ManyToManyField(
        'Recipe',
        through='UserRecipeFavorite',
        related_name='favorited_by',
        verbose_name='Избранные рецепты')
    in_shopping_list = models.ManyToManyField(
        'Recipe',
        through='UserRecipeShoppingList',
        related_name='in_shopping_list_by',
        verbose_name='Рецепты в листе покупок')

    objects = AddOptionsUserQuerySet().as_manager()

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
        related_name='subscriptions_many_table',
        verbose_name='Подписан на')
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers_many_table',
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


class RecipeIngredient(models.Model):
    """Many to many recipes to ingredients model with amount."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_many_table',
        verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.PROTECT,
        related_name='recipe_many_table',
        verbose_name='Ингредиент')
    amount = models.IntegerField(
        verbose_name='Количество', validators=(
            MinValueValidator(
                limit_value=settings.MIN_AMOUNT, message=(
                    'Количество ингредиента должно быть не меньше '
                    f'{settings.MIN_COOKING_TIME} единицы')),))

    class Meta:
        verbose_name = 'Ингрединт в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                name='recipe_ingredient_unique',
                fields=['recipe', 'ingredient']
            ),
        ]

    def __str__(self):
        return (f'{self.recipe} содержит {self.ingredient} в '
                f'количестве {self.amount} {self.ingredient.measurement_unit}')


class RecipeTag(models.Model):
    """Many to many recipes to tags model."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Рецепт')
    tag = models.ForeignKey(
        'Tag',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name='Тег')

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        constraints = [
            models.UniqueConstraint(
                name='recipe_tag_unique',
                fields=['recipe', 'tag']
            ),
        ]

    def __str__(self):
        return f'К {self.recipe} подключен тег {self.tag}'


class Recipe(models.Model):
    """Model for recipes."""

    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    ingredients = models.ManyToManyField(
        'Ingredient',
        related_name='used_in_recipes',
        through='RecipeIngredient',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        through='RecipeTag',
        verbose_name='Теги')
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/')
    name = models.CharField(
        verbose_name='Название',
        max_length=settings.MAX_RECIPE_NAME)
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=(MinValueValidator(
            limit_value=settings.MIN_COOKING_TIME,
            message=('Время приготовления должно быть не меньше '
                     f'{settings.MIN_COOKING_TIME} минут')
        ),))

    objects = AddOptionsRecipeQuerySet().as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class UserRecipeFavorite(models.Model):
    """Model for favorite recipe."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='favorited_many_table',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='favorites_many_table',
        verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                name='recipe_user_favorite_unique',
                fields=['recipe', 'user']
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class UserRecipeShoppingList(models.Model):
    """Model for recipe in shopping list."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='shopped_many_table',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='shopping_many_table',
        verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                name='recipe_user_shopping_unique',
                fields=['recipe', 'user']
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'
