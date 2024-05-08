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
from .permissions import IsAdminOrAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, ShortRecipeSerializer,
                          TagSerializer)
from .mixins import CreateListDestroyViewSet, ListRetrieveViewSet

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = CustomUserShortSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    @action(('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        """Функция работы с адресом me."""
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)


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
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Метод создания подписки."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscribe = get_object_or_404(User, id=self.kwargs['user_id'])
        if self.request.user == subscribe:
            raise ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(
            user=self.request.user, subscribe=subscribe
        ):
            raise ValidationError('Вы уже подписаны на этого автора')
        serializer.save(user=self.request.user, subscribe=subscribe)
        headers = self.get_success_headers(serializer.data)
        return Response(CustomUserFullSerializer(
            get_object_or_404(User, pk=self.kwargs['user_id']),
            context={'request': request}).data,
            status=status.HTTP_201_CREATED, headers=headers)

    @action(('DELETE',), detail=True)
    def delete(self, request, user_id):
        """Метод удаления подписки."""
        get_object_or_404(User, id=user_id)
        subscription = Subscription.objects.filter(
            user=request.user, subscribe__id=user_id)
        if not subscription:
            raise ValidationError('Данной подписки не существует')
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(ListRetrieveViewSet):
    """Вьюсет для работы с моделью тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ListRetrieveViewSet):
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
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=('POST', 'DELETE'),
            permission_classes=(IsAuthenticated, ))
    def favorite(self, request, pk):
        """Метод добавления и удаления рецепта в избранном."""
        if request.method == 'POST':
            recipe = Recipe.objects.filter(pk=pk).first()
            if not recipe:
                raise ValidationError('Такого рецепта не существует')
            if Favorite.objects.filter(user=request.user, recipe=recipe):
                raise ValidationError('Рецепт уже есть в избранном.')
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe)
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError('Рецепт не добавлен в избранное')

    @action(detail=True, methods=('POST', 'DELETE'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """Метод добавления и удаления рецепта в списке покупок."""
        if request.method == 'POST':
            recipe = Recipe.objects.filter(pk=pk).first()
            if not recipe:
                raise ValidationError('Такого рецепта не существует')
            if ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe):
                raise ValidationError('Рецепт уже есть в списке покупок.')
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe)
        if shopping_cart:
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError('Рецепт не добавлен в избранное')

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
