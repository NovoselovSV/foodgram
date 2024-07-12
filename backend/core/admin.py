from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

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

admin.site.register(Subscription)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)
admin.site.register(UserRecipeShoppingList)
admin.site.register(UserRecipeFavorite)
admin.site.register(RecipeTag)
admin.site.register(Recipe)
admin.site.register(User, UserAdmin)
