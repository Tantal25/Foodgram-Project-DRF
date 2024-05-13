
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription
from .utils import recipe_ingredient_create

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода коротких данных о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserShortSerializer(UserSerializer):
    """Сериализатор для работы с профилями пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, object):
        """Метод для вывода подписки на пользователя."""
        return bool(self.context['request'].user.is_authenticated
                    and Subscription.objects.filter(
                        user=self.context['request'].user,
                        subscribe=object).exists())


class CustomUserFullSerializer(CustomUserShortSerializer):
    """Сериализатор для работы с профилями пользователя."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserShortSerializer.Meta):
        fields = CustomUserShortSerializer.Meta.fields + [
            'recipes', 'recipes_count']

    def get_recipes(self, object):
        recipes = Recipe.objects.filter(author=object)
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        serializers = ShortRecipeSerializer(recipes, many=True)
        return serializers.data

    def get_recipes_count(self, object):
        """Метод выводящий количество рецептов у пользователя."""
        return Recipe.objects.filter(author=object).count()


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с подписками пользователей."""

    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault())
    subscribe = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('user', 'subscribe')

    def validate(self, data):
        if self.context['request'].user == self.initial_data['subscribe']:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(
            user=self.context['request'].user,
            subscribe=self.initial_data['subscribe']
        ):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора')
        return data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для проемежуточной модели рецепта - ингредиента."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', "name", "measurement_unit", "amount")


class IngredientsAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецепта-ингредиента с добавлением количества."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=[MinValueValidator(
            1.0,
            message='Количество ингредиента не может быть меньше 1')]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецепта."""

    author = CustomUserShortSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredients')
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Метод для отображения нахождения рецепта в избранном."""
        return bool(self.context['request'].user.is_authenticated
                    and Favorite.objects.filter(
                        user=self.context['request'].user,
                        recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        """Метод для отображения нахождения рецепта в списке покупок."""
        return bool(self.context['request'].user.is_authenticated
                    and ShoppingCart.objects.filter(
                        user=self.context['request'].user,
                        recipe=obj).exists())


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    author = CustomUserFullSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientsAmountSerializer(many=True, required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'author',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент для рецепта')
        ingredient_list = []
        for ingredient in data['ingredients']:
            ingredient_exist = Ingredient.objects.filter(id=ingredient['id'])
            if not ingredient_exist:
                raise serializers.ValidationError(
                    'Такого ингредиента не существует')
            if ingredient['id'] in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться')
            ingredient_list.append(ingredient['id'])
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Нужен хотя бы один тег для рецепта')
        tag_list = []
        for tag in data['tags']:
            if tag in tag_list:
                raise serializers.ValidationError('Теги не должны повторяться')
            tag_list.append(tag)
        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'У рецепта должно быть изображение')
        return value

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data)
        recipe.tags.set(tags)
        recipe_ingredient_create(ingredients, instance=recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        recipe_ingredient_create(ingredients, instance)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if Favorite.objects.filter(user=data['user'], recipe=data['recipe']):
            raise serializers.ValidationError('Рецепт уже есть в избранном.')
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if ShoppingCart.objects.filter(
            user=data['user'], recipe=data['recipe']
        ):
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок.')
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(instance.recipe, context={
            'request': self.context.get('request')
        }).data
