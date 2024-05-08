from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    SubscriveViewSet, TagsViewSet)

router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users/(?P<user_id>\d+)/subscribe',
                SubscriveViewSet,
                basename='subscribe')
router.register(r'users/subscriptions',
                SubscriveViewSet,
                basename='subscriptions')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
