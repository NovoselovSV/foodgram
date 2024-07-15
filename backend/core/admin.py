from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


class SearchableUserAdmin(UserAdmin):
    """Custom display for user model in admin zone."""

    search_fields = ('username', 'email')


class RecipeAdmin(admin.ModelAdmin):
    """Custom display for recipe model in admin zone."""

    search_fields = ('author__username', 'name')
    list_filter = ('tags',)
    readonly_fields = ('is_favorited_count',)

    @admin.display(description='Количество добавленных в избранное')
    def is_favorited_count(self, recipe):
        return recipe.favorited_by.count()


class IngredientAdmin(admin.ModelAdmin):
    """Custom display for ingredient model in admin zone."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(models.Subscription)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.RecipeIngredient)
admin.site.register(models.UserRecipeShoppingList)
admin.site.register(models.UserRecipeFavorite)
admin.site.register(models.RecipeTag)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.User, SearchableUserAdmin)
