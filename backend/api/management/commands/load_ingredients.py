import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда загружающая в БД ингредиенты из csv файла в папке data."""

    def handle(self, *args, **kwargs):
        with open('data/ingredients.csv',
                  'r', encoding='UTF-8') as ingredients:
            reader = csv.reader(ingredients)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row[0], measurement_unit=row[1])
