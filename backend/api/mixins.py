from rest_framework import mixins, viewsets

from .validation import validate_username


class CreateListDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Миксин для вьюсета подписок."""

    pass


class ListRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Миксин для вьюсетов Тега и Ингредиентов."""

    pass


class ValidateUsernameMixin:
    """Миксин для валидации юзернейма пользователя."""

    def validate_username(self, value):
        """Метод валидации юзернейма."""
        return validate_username(value)
