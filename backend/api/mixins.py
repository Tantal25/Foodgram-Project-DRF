from rest_framework import mixins, viewsets


class CreateListDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Миксин для вьюсета подписок."""

    pass
