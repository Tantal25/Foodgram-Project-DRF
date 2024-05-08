from django.contrib.auth.models import AbstractUser
from django.db import models

from api.validation import validate_username

from .constants import EXTENDED_FIELD_LENGTH, STANDARD_FIELD_LENGTH


class User(AbstractUser):
    """Переопределенная модель пользователя."""

    email = models.EmailField(
        max_length=EXTENDED_FIELD_LENGTH,
        unique=True,
        verbose_name='Почта'
    )
    username = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        unique=True,
        verbose_name='Имя пользователя',
        validators=(validate_username, )
    )
    first_name = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок на других пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    subscribe = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='subscribe'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribe'],
                name='unique_user_subscribe'),
            models.CheckConstraint(
                name='api_prevent_self_subscribe',
                check=~models.Q(user=models.F('subscribe')),
            ),
        ]
