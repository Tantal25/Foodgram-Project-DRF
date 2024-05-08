import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

from .mixins import ValidateUsernameMixin

User = get_user_model()


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного и списка покупок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserRegistrationSerializer(UserCreateSerializer, ValidateUsernameMixin):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password',
        )


class CustomUserShortSerializer(UserSerializer, ValidateUsernameMixin):
    """Сериализатор для работы с профилями пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, object):
        """Метод для вывода подписки на пользователя."""
        request = self.context['request']
        if request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, subscribe=object).exists()
        return False


class CustomUserFullSerializer(CustomUserShortSerializer):
    """Сериализатор для работы с профилями пользователя."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def get_recipes(self, object):
        recipes = Recipe.objects.filter(author=object)
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
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


class Base64Image(serializers.ImageField):
    """Сериализатор для работы с изображениями."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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
    amount = serializers.IntegerField()

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
    image = Base64Image(required=True, allow_null=False)
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
        request = self.context['request']
        if request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Метод для отображения нахождения рецепта в списке покупок."""
        request = self.context['request']
        if request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецептов."""

    author = CustomUserFullSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientsAmountSerializer(many=True)
    image = Base64Image()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'author',
                  'name', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент для рецепта')
        ingredient_list = []
        for ingredient in value:
            ingredient_exist = Ingredient.objects.filter(id=ingredient['id'])
            if not ingredient_exist:
                raise serializers.ValidationError(
                    'Такой ингредиент не существует')
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше единицы')
            if ingredient['id'] in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться')
            ingredient_list.append(ingredient['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один тег для рецепта')
        tag_list = []
        for tag in value:
            tag_exist = get_object_or_404(Tag, name=tag)
            if tag_exist in tag_list:
                raise serializers.ValidationError(
                    'Теги не должны повторяться')
            tag_list.append(tag_exist)
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше единицы')
        return value

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            amount = ingredient.pop('amount')
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=amount)
        return recipe

    def update(self, instance, validated_data):
        if not validated_data.get('ingredients'):
            raise serializers.ValidationError('Не добавлены ингредиенты')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        if not validated_data.get('tags'):
            raise serializers.ValidationError('Не добавлены теги')
        tags = validated_data.pop('tags')
        if tags:
            instance.tags.set(tags)
        for ingredient in ingredients:
            amount = ingredient.pop('amount')
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient['id'])
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=current_ingredient,
                amount=amount)
        return super().update(instance, validated_data)
