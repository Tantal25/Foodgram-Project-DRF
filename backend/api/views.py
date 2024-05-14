from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.serializers import (CustomUserFullSerializer,
                             CustomUserShortSerializer, SubscribeSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription
from .filters import IngredientNameFilter, RecipeFilter
from .mixins import CreateListDestroyViewSet
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = CustomUserShortSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    @action(('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        """Функция работы с адресом me."""
        return super().me(request, *args, **kwargs)


class SubscriveViewSet(CreateListDestroyViewSet):
    """Вьюсет для работы с подписками."""

    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """Метод получения подписчиков пользователя."""
        return self.request.user.subscriber.all()

    def list(self, request, *args, **kwargs):
        """Метод вывода списка подписчиков пользователя."""
        queryset = self.filter_queryset(User.objects.filter(
            subscribe__user=self.request.user))
        page = self.paginate_queryset(queryset)
        serializer = CustomUserFullSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Метод создания подписки."""
        subscribe = get_object_or_404(User, id=self.kwargs['user_id'])
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'subscribe': subscribe.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        """Метод удаления подписки."""
        get_object_or_404(User, id=kwargs['user_id'])
        subscription, _ = Subscription.objects.filter(
            user=request.user, subscribe__id=kwargs['user_id']).delete()
        if not subscription:
            raise ValidationError('Данной подписки не существует')
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с моделью тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с моделью ингредиента."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientNameFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с моделью рецепта."""

    http_method_not_allowed = ('PUT',)
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminOrAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action == 'create' or 'partial_update':
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    @action(detail=True,
            methods=('POST',),
            permission_classes=(IsAuthenticated, ))
    def favorite(self, request, pk):
        """Метод добавления и удаления рецепта в избранном."""
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response('Данного рецепта не существует',
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteSerializer(
            data={'recipe': recipe.id, 'user': request.user.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not favorite:
            raise ValidationError('Рецепт не добавлен в избранное')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """Метод добавления и удаления рецепта в списке покупок."""
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response('Данного рецепта не существует',
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id, 'user': request.user.id},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart, _ = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe).delete()
        if not shopping_cart:
            raise ValidationError('Рецепт не добавлен в список покупок')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('GET',))
    def download_shopping_cart(self, request):
        """Метод отправляющий список покупок пользователю."""
        shopping_cart = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    ingredient_sum=Sum('amount'))
        cart = 'Список покупок:\n'
        counter = 0
        for ingredient in shopping_cart:
            counter += 1
            cart += (f"{counter}) {ingredient['ingredient__name']}"
                     f" ({ingredient['ingredient__measurement_unit']}) - "
                     f"{ingredient['ingredient_sum']} \n"
                     )
        response = HttpResponse(cart, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_cart.txt"')
        return response
