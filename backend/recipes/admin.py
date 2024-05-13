from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'is_favorited', 'pub_date')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    inlines = [IngredientInline]

    @admin.display(description='Добавлен в избранное')
    def is_favorited(self, obj):
        """Метод выводящий количество добавлений рецепта в избранное."""
        return obj.favorites.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
