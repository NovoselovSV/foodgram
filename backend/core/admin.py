from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Subscription,
    Tag,
    User,
    UserRecipeFavorite,
    UserRecipeShoppingList)


class CustomUserAdmin(UserAdmin):
    search_fields = ('username', 'email')


class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('author.username', 'name')
    list_filter = ('tags',)
    readonly_fields = ('is_favorited_count',)

    @admin.display(description='Количество добавленных в избранное')
    def is_favorited_count(self, recipe):
        return recipe.favorited_by.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Subscription)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(UserRecipeShoppingList)
admin.site.register(UserRecipeFavorite)
admin.site.register(RecipeTag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(User, CustomUserAdmin)
