from django.core.management.base import BaseCommand

from recipes.models import Tag

TAG_DATA = [
    {'name': 'Завтрак', 'color': '#DC143C', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#FFD700', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#C71585', 'slug': 'dinner'}
]


class Command(BaseCommand):
    """Команда создающая в базе данных несколько тегов для рецептов."""

    def handle(self, *args, **kwargs):
        for tag in TAG_DATA:
            Tag.objects.create(**tag)
            self.stdout.write(
                self.style.SUCCESS(f'Тэг {tag} успешно добавлен')
            )
