from recipes.models import RecipeIngredient


def recipe_ingredient_create(ingredients, instance):
    """Метод который создает связь ингредиентов с рецептом."""
    for ingredient in ingredients:
        RecipeIngredient(
                ingredient_id=ingredient['id'],
                recipe=instance,
                amount=ingredient['amount']
            )
