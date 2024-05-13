from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram_backend.constants import (MEDIUM_FIELD_LENGTH,
                                        STANDARD_FIELD_LENGTH)

User = get_user_model()


class Tag(models.Model):
    """Модель тэга."""

    name = models.CharField(
        verbose_name='Название тега',
        unique=True,
        max_length=MEDIUM_FIELD_LENGTH
    )
    color = ColorField(
        format='hex',
        verbose_name='Цвет',
        unique=True,
        max_length=STANDARD_FIELD_LENGTH
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        max_length=MEDIUM_FIELD_LENGTH
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название ингрeдиента',
        max_length=MEDIUM_FIELD_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=MEDIUM_FIELD_LENGTH
    )

    class Meta:
        verbose_name = 'ингрeдиент'
        verbose_name_plural = 'Ингрeдиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_unit')]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField(
        max_length=MEDIUM_FIELD_LENGTH,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Введите время приготовления блюда в минутах.',
        validators=[
            MinValueValidator(
                1.0, message='Время готовки не может быть меньше 1'),
            MaxValueValidator(
                32000, message='Время готовки не может быть больше 32000')
        ]
    )
    image = models.ImageField(
        upload_to='api/media/',
        verbose_name='Изображение'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингрeдиенты',
        related_name='recipes',
        through='RecipeIngredient'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингрeдиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингрeдиент',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                1.0, message='Количество ингредиентов не может быть меньше 1'),
            MaxValueValidator(
                32000,
                message='Количество ингредиентов не может быть больше 32000')
        ]
    )

    def __str__(self):
        return f'{self.ingredient} - {self.recipe}'


class Favorite(models.Model):
    """Модель для добавления рецепта в избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_favorites')]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Модель для добавления рецепта в список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_carts'
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_shopping_carts')]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
